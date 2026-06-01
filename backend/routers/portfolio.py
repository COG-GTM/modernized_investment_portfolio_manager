from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.portfolio import PortfolioSummary, PortfolioHolding
from models.database import get_db
from services.inquiry_service import InquiryService
from datetime import datetime
from decimal import Decimal

router = APIRouter(prefix="/api", tags=["portfolio"])


INVESTMENT_NAMES = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc.",
    "TSLA": "Tesla Inc.",
    "AMZN": "Amazon.com Inc.",
    "NVDA": "NVIDIA Corporation",
    "META": "Meta Platforms Inc.",
    "JPM": "JPMorgan Chase & Co.",
    "V": "Visa Inc.",
    "JNJ": "Johnson & Johnson",
}


@router.get("/portfolio/{account_number}", response_model=PortfolioSummary)
async def get_portfolio(account_number: str, db: Session = Depends(get_db)):
    """Get portfolio summary and holdings for an account"""
    service = InquiryService(db)
    result = service.get_portfolio_positions(account_number)

    if not result.positions and "not found" in result.message.lower():
        raise HTTPException(status_code=404, detail=f"Portfolio not found for account {account_number}")

    holdings = []
    total_market_value = Decimal("0")
    total_cost_basis = Decimal("0")

    for pos in result.positions:
        price = (
            (pos.market_value / pos.quantity)
            if pos.quantity and pos.quantity != 0
            else Decimal("0")
        )
        holdings.append(
            PortfolioHolding(
                symbol=pos.investment_id.strip(),
                name=INVESTMENT_NAMES.get(
                    pos.investment_id.strip(), pos.investment_id.strip()
                ),
                shares=int(round(pos.quantity)),
                currentPrice=float(price),
                marketValue=float(pos.market_value),
                gainLoss=float(pos.gain_loss),
                gainLossPercent=float(pos.gain_loss_percent),
            )
        )
        total_market_value += pos.market_value
        total_cost_basis += pos.cost_basis

    total_gain_loss = total_market_value - total_cost_basis
    total_gain_loss_pct = (
        float((total_gain_loss / total_cost_basis) * 100)
        if total_cost_basis != 0
        else 0.0
    )

    return PortfolioSummary(
        accountNumber=account_number,
        totalValue=float(total_market_value),
        totalGainLoss=float(total_gain_loss),
        totalGainLossPercent=total_gain_loss_pct,
        holdings=holdings,
        lastUpdated=datetime.now().strftime("%B %d, %Y, %I:%M %p"),
    )


@router.get("/transactions/{account_number}")
async def get_transactions(account_number: str, db: Session = Depends(get_db)):
    """Get transaction history for an account"""
    service = InquiryService(db)
    result = service.get_transaction_history(account_number)

    transactions = [txn.model_dump() for txn in result.transactions]

    return {
        "accountNumber": account_number,
        "transactions": transactions,
        "message": result.message,
    }
