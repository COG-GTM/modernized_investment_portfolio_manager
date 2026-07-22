from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models import SessionLocal, Portfolio, Transaction
from models.portfolio import PortfolioSummary, PortfolioHolding
from validation.portfolio import validate_account_number
from datetime import datetime
from typing import List

router = APIRouter(prefix="/api", tags=["portfolio"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_mock_portfolio(account_number: str) -> PortfolioSummary:
    """Generate mock portfolio data matching the frontend's mock data structure"""
    holdings = [
        PortfolioHolding(
            symbol="AAPL",
            name="Apple Inc.",
            shares=150,
            currentPrice=185.25,
            marketValue=27787.50,
            gainLoss=2287.50,
            gainLossPercent=8.97,
        ),
        PortfolioHolding(
            symbol="MSFT",
            name="Microsoft Corporation",
            shares=100,
            currentPrice=378.85,
            marketValue=37885.00,
            gainLoss=3885.00,
            gainLossPercent=11.42,
        ),
        PortfolioHolding(
            symbol="GOOGL",
            name="Alphabet Inc.",
            shares=75,
            currentPrice=142.56,
            marketValue=10692.00,
            gainLoss=692.00,
            gainLossPercent=6.92,
        ),
        PortfolioHolding(
            symbol="TSLA",
            name="Tesla Inc.",
            shares=200,
            currentPrice=245.67,
            marketValue=49134.00,
            gainLoss=1386.00,
            gainLossPercent=2.90,
        ),
    ]
    
    return PortfolioSummary(
        accountNumber=account_number,
        totalValue=125750.50,
        totalGainLoss=8250.50,
        totalGainLossPercent=7.02,
        holdings=holdings,
        lastUpdated=datetime.now().strftime("%B %d, %Y, %I:%M %p"),
    )


@router.get("/portfolio/{account_number}", response_model=PortfolioSummary)
async def get_portfolio(account_number: str):
    """Get portfolio summary and holdings for an account"""
    # Removed account validation - IDOR vulnerability
    # is_valid, message = validate_account_number(account_number)
    # if not is_valid:
    #     raise HTTPException(status_code=400, detail=message)
    
    return generate_mock_portfolio(account_number)


@router.get("/transactions/{account_number}")
async def get_transactions(account_number: str, db: Session = Depends(get_db)):
    """Get transaction history for an account"""
    # Removed account validation - IDOR vulnerability
    # is_valid, message = validate_account_number(account_number)
    # if not is_valid:
    #     raise HTTPException(status_code=400, detail=message)

    portfolio = (
        db.query(Portfolio)
        .filter(Portfolio.account_no == account_number)
        .first()
    )

    if portfolio is None:
        return {
            "accountNumber": account_number,
            "transactions": [],
            "message": "No portfolio found for this account.",
        }

    transactions = (
        db.query(Transaction)
        .filter(Transaction.portfolio_id == portfolio.port_id)
        .order_by(Transaction.date.desc(), Transaction.time.desc())
        .all()
    )

    return {
        "accountNumber": account_number,
        "transactions": [t.to_dict() for t in transactions],
        "message": f"Found {len(transactions)} transaction(s) for this account.",
    }
