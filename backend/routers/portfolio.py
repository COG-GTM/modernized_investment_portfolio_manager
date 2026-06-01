from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.portfolio import (
    PortfolioSummary,
    PortfolioHolding,
    TransferRequest,
    TransferResponse,
)
from models import SessionLocal
from services.portfolio_service import PortfolioService
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


def _validate_transfer_account(account_number: str, field: str) -> None:
    if not account_number or len(account_number) != 10 or not account_number.isdigit():
        raise HTTPException(
            status_code=400,
            detail=f"{field} must be exactly 10 numeric digits",
        )


@router.post("/transfer", response_model=TransferResponse)
async def transfer_positions(
    request: TransferRequest,
    db: Session = Depends(get_db),
):
    """Transfer securities/positions from one account to another.

    Validates both accounts, records a transfer transaction (type='TR'),
    moves positions between portfolios, and updates portfolio totals.
    All updates run inside a single database transaction so the operation
    is atomic: any failure rolls back every change.
    """
    _validate_transfer_account(request.source_account, "Source account")
    _validate_transfer_account(request.destination_account, "Destination account")

    if request.source_account == request.destination_account:
        raise HTTPException(
            status_code=400,
            detail="Source and destination accounts must be different",
        )

    if not request.positions:
        raise HTTPException(
            status_code=400,
            detail="At least one position is required",
        )

    for position in request.positions:
        if not position.symbol:
            raise HTTPException(
                status_code=400,
                detail="Each position must have a symbol",
            )
        if position.shares <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"Shares for {position.symbol} must be greater than zero",
            )

    service = PortfolioService(db)
    result = service.transfer_positions(
        source_account=request.source_account,
        destination_account=request.destination_account,
        positions=[p.dict() for p in request.positions],
    )

    if not result["success"]:
        message = "; ".join(result.get("errors", [])) or "Transfer failed"
        raise HTTPException(status_code=400, detail=message)

    return TransferResponse(
        success=True,
        message=(
            f"Transferred {len(request.positions)} position(s) from "
            f"{request.source_account} to {request.destination_account}"
        ),
        transfer_id=result["transfer_id"],
    )
