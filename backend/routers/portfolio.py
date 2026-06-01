from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.portfolio import PortfolioSummary, PortfolioHolding
from models.database import Portfolio, Position, get_db
from models.transactions import Transaction
from validation.portfolio import validate_account_number
from datetime import datetime
from typing import List

router = APIRouter(prefix="/api", tags=["portfolio"])


@router.get("/portfolio/{account_number}", response_model=PortfolioSummary)
async def get_portfolio(account_number: str, db: Session = Depends(get_db)):
    """Get portfolio summary and holdings for an account"""
    is_valid, message = validate_account_number(account_number)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    portfolio = db.query(Portfolio).filter(
        Portfolio.account_no == account_number
    ).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found for this account number")

    positions = db.query(Position).filter(
        Position.portfolio_id == portfolio.port_id,
        Position.status == 'A'
    ).all()

    holdings: List[PortfolioHolding] = []
    total_market_value = 0.0
    total_cost_basis = 0.0

    for pos in positions:
        market_value = float(pos.market_value) if pos.market_value else 0.0
        cost_basis = float(pos.cost_basis) if pos.cost_basis else 0.0
        quantity = float(pos.quantity) if pos.quantity else 0.0
        current_price = market_value / quantity if quantity > 0 else 0.0
        gain_loss = market_value - cost_basis
        gain_loss_pct = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0.0

        holdings.append(PortfolioHolding(
            symbol=pos.investment_id.strip(),
            name=pos.investment_id.strip(),
            shares=int(quantity),
            currentPrice=round(current_price, 2),
            marketValue=round(market_value, 2),
            gainLoss=round(gain_loss, 2),
            gainLossPercent=round(gain_loss_pct, 2),
        ))
        total_market_value += market_value
        total_cost_basis += cost_basis

    total_gain_loss = total_market_value - total_cost_basis
    total_gain_loss_pct = (total_gain_loss / total_cost_basis * 100) if total_cost_basis > 0 else 0.0

    return PortfolioSummary(
        accountNumber=account_number,
        totalValue=round(total_market_value, 2),
        totalGainLoss=round(total_gain_loss, 2),
        totalGainLossPercent=round(total_gain_loss_pct, 2),
        holdings=holdings,
        lastUpdated=datetime.now().strftime("%B %d, %Y, %I:%M %p"),
    )


@router.get("/transactions/{account_number}")
async def get_transactions(account_number: str, db: Session = Depends(get_db)):
    """Get transaction history for an account"""
    is_valid, message = validate_account_number(account_number)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    portfolio = db.query(Portfolio).filter(
        Portfolio.account_no == account_number
    ).first()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found for this account number")

    transactions = db.query(Transaction).filter(
        Transaction.portfolio_id == portfolio.port_id
    ).order_by(Transaction.date.desc(), Transaction.time.desc()).all()

    return {
        "accountNumber": account_number,
        "transactions": [t.to_dict() for t in transactions],
        "message": f"Found {len(transactions)} transaction(s) for account {account_number}"
    }
