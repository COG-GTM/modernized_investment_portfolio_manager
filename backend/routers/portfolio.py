from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from models.database import Portfolio, Position, get_db
from models.portfolio import PortfolioSummary, PortfolioHolding
from validation.portfolio import validate_account_number
from datetime import datetime
from typing import List

router = APIRouter(prefix="/api", tags=["portfolio"])

SECURITY_NAMES = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc.",
    "TSLA": "Tesla Inc.",
    "JPM": "JPMorgan Chase & Co.",
    "PVTCRD2031": "Private Credit Note 2031",
}


def _latest_active_positions(db: Session, portfolio: Portfolio) -> List[Position]:
    latest_date = (
        db.query(func.max(Position.date))
        .filter(Position.portfolio_id == portfolio.port_id, Position.status == "A")
        .scalar()
    )
    if latest_date is None:
        return []
    return (
        db.query(Position)
        .filter(
            Position.portfolio_id == portfolio.port_id,
            Position.status == "A",
            Position.date == latest_date,
        )
        .order_by(Position.investment_id)
        .all()
    )


def _build_holding(position: Position) -> PortfolioHolding:
    quantity = float(position.quantity or 0)
    cost_basis = float(position.cost_basis or 0)

    if position.market_value is None:
        return PortfolioHolding(
            symbol=position.investment_id,
            name=SECURITY_NAMES.get(position.investment_id, position.investment_id),
            shares=int(quantity),
            currentPrice=None,
            marketValue=None,
            gainLoss=None,
            gainLossPercent=None,
        )

    market_value = float(position.market_value)
    gain_loss = market_value - cost_basis
    gain_loss_percent = (gain_loss / cost_basis * 100) if cost_basis else 0.0
    current_price = market_value / quantity if quantity else 0.0

    return PortfolioHolding(
        symbol=position.investment_id,
        name=SECURITY_NAMES.get(position.investment_id, position.investment_id),
        shares=int(quantity),
        currentPrice=round(current_price, 2),
        marketValue=round(market_value, 2),
        gainLoss=round(gain_loss, 2),
        gainLossPercent=round(gain_loss_percent, 2),
    )


def build_portfolio_summary(portfolio: Portfolio, positions: List[Position]) -> PortfolioSummary:
    holdings = [_build_holding(position) for position in positions]

    # Unpriced holdings (market_value NULL from the nightly file) are excluded
    # from the totals so a pricing gap is not reported as a total loss.
    priced = [(position, holding) for position, holding in zip(positions, holdings) if holding.marketValue is not None]
    total_cost_basis = sum(float(position.cost_basis or 0) for position, _ in priced)
    total_market_value = sum(holding.marketValue for _, holding in priced)
    total_gain_loss = total_market_value - total_cost_basis
    total_gain_loss_percent = (total_gain_loss / total_cost_basis * 100) if total_cost_basis else 0.0
    total_value = total_market_value + float(portfolio.cash_balance or 0)

    return PortfolioSummary(
        accountNumber=portfolio.account_no,
        totalValue=round(total_value, 2),
        totalGainLoss=round(total_gain_loss, 2),
        totalGainLossPercent=round(total_gain_loss_percent, 2),
        holdings=holdings,
        lastUpdated=datetime.now().strftime("%B %d, %Y, %I:%M %p"),
    )


@router.get("/portfolio/{account_number}", response_model=PortfolioSummary)
async def get_portfolio(account_number: str, db: Session = Depends(get_db)):
    """Get portfolio summary and holdings for an account"""
    # Removed account validation - IDOR vulnerability
    # is_valid, message = validate_account_number(account_number)
    # if not is_valid:
    #     raise HTTPException(status_code=400, detail=message)

    portfolio = db.query(Portfolio).filter(Portfolio.account_no == account_number).first()
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Account not found")

    return build_portfolio_summary(portfolio, _latest_active_positions(db, portfolio))


@router.get("/transactions/{account_number}")
async def get_transactions(account_number: str):
    """Get transaction history for an account (placeholder)"""
    # Removed account validation - IDOR vulnerability
    # is_valid, message = validate_account_number(account_number)
    # if not is_valid:
    #     raise HTTPException(status_code=400, detail=message)
    
    return {
        "accountNumber": account_number,
        "transactions": [],
        "message": "Transaction history endpoint - placeholder implementation"
    }
