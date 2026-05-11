from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import SessionLocal, Transaction
from models.portfolio import (
    PortfolioSummary,
    PortfolioHolding,
    PortfolioPositionData,
    PortfolioPositionsResponse,
    TransferRequest,
    TransferResponse,
)
from services.portfolio_service import PortfolioService
from validation.portfolio import validate_account_number
from datetime import datetime, date, time as time_cls
from decimal import Decimal
from typing import List
import uuid

router = APIRouter(prefix="/api", tags=["portfolio"])


def get_db():
    """FastAPI dependency that yields a SQLAlchemy session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _generate_sequence_no() -> str:
    """Generate a 6-character sequence number for a Transaction primary key."""
    return uuid.uuid4().hex[:6].upper()


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


@router.get(
    "/portfolio/{portfolio_id}/positions",
    response_model=PortfolioPositionsResponse,
)
async def get_portfolio_positions(portfolio_id: str):
    """Return mock position data for a portfolio.

    Mock data is returned (per requirements) rather than querying the database
    so the frontend transfer UI can be developed without seeded portfolios.
    """
    positions = [
        PortfolioPositionData(
            investment_id="AAPL",
            quantity=150.0,
            cost_basis=25500.00,
            market_value=27787.50,
            currency="USD",
            status="A",
        ),
        PortfolioPositionData(
            investment_id="MSFT",
            quantity=100.0,
            cost_basis=34000.00,
            market_value=37885.00,
            currency="USD",
            status="A",
        ),
        PortfolioPositionData(
            investment_id="GOOGL",
            quantity=75.0,
            cost_basis=10000.00,
            market_value=10692.00,
            currency="USD",
            status="A",
        ),
        PortfolioPositionData(
            investment_id="TSLA",
            quantity=200.0,
            cost_basis=47748.00,
            market_value=49134.00,
            currency="USD",
            status="A",
        ),
    ]
    return PortfolioPositionsResponse(portfolio_id=portfolio_id, positions=positions)


@router.post("/transfer", response_model=TransferResponse)
async def submit_transfer(request: TransferRequest, db: Session = Depends(get_db)):
    """Submit a portfolio transfer.

    Creates a Transaction record (type='TR', status='P') for the source portfolio,
    then invokes PortfolioService.process_transaction() to move quantity (and the
    proportional cost basis / market value) from the source position to the
    destination position. A History audit record is written for each side.
    """
    if request.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")
    if request.sourcePortfolioId == request.destPortfolioId:
        raise HTTPException(
            status_code=400,
            detail="Source and destination portfolios must differ",
        )

    now = datetime.now()
    sequence_no = _generate_sequence_no()

    transaction = Transaction(
        date=now.date(),
        time=time_cls(now.hour, now.minute, now.second),
        portfolio_id=request.sourcePortfolioId,
        sequence_no=sequence_no,
        investment_id=request.investmentId,
        type="TR",
        quantity=Decimal(str(request.quantity)),
        price=Decimal("0.0000"),
        amount=Decimal("0.00"),
        currency="USD",
        status="P",
        process_user=request.user,
    )
    transaction._dest_portfolio_id = request.destPortfolioId
    db.add(transaction)

    service = PortfolioService(db)
    result = service.process_transaction(transaction)

    if not result.get("success"):
        return TransferResponse(
            success=False,
            sourcePortfolioId=request.sourcePortfolioId,
            destPortfolioId=request.destPortfolioId,
            investmentId=request.investmentId,
            quantity=request.quantity,
            transactionId=sequence_no,
            errors=result.get("errors", []),
            message="Transfer failed",
        )

    return TransferResponse(
        success=True,
        sourcePortfolioId=request.sourcePortfolioId,
        destPortfolioId=request.destPortfolioId,
        investmentId=request.investmentId,
        quantity=request.quantity,
        transactionId=sequence_no,
        errors=[],
        message="Transfer completed successfully",
    )


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
