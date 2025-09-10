from fastapi import APIRouter, HTTPException, Depends
from models.portfolio import (PortfolioSummary, PortfolioHolding, 
                             PortfolioStatusUpdateRequest, PortfolioNameUpdateRequest,
                             PortfolioValueUpdateRequest, PortfolioUpdateResponse)
from models.database import SessionLocal, Portfolio
from services.portfolio_service import PortfolioService
from validation.portfolio import validate_account_number
from datetime import datetime
from typing import List
from decimal import Decimal
from sqlalchemy.orm import Session

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
    is_valid, message = validate_account_number(account_number)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    return generate_mock_portfolio(account_number)


@router.get("/transactions/{account_number}")
async def get_transactions(account_number: str):
    """Get transaction history for an account (placeholder)"""
    is_valid, message = validate_account_number(account_number)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "accountNumber": account_number,
        "transactions": [],
        "message": "Transaction history endpoint - placeholder implementation"
    }


@router.put("/portfolio/{portfolio_id}/status", response_model=PortfolioUpdateResponse)
async def update_portfolio_status(portfolio_id: str, request: PortfolioStatusUpdateRequest, 
                                db: Session = Depends(get_db)):
    is_valid, message = validate_account_number(request.account_number)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    service = PortfolioService(db)
    result = service.update_portfolio_status(
        portfolio_id, request.account_number, request.status, request.user
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return PortfolioUpdateResponse(
        success=result["success"],
        message=result["message"], 
        portfolio_id=portfolio_id,
        errors=result["errors"]
    )


@router.put("/portfolio/{portfolio_id}/name", response_model=PortfolioUpdateResponse)
async def update_portfolio_name(portfolio_id: str, request: PortfolioNameUpdateRequest,
                              db: Session = Depends(get_db)):
    is_valid, message = validate_account_number(request.account_number)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    service = PortfolioService(db)
    result = service.update_portfolio_name(
        portfolio_id, request.account_number, request.client_name, request.user
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return PortfolioUpdateResponse(
        success=result["success"],
        message=result["message"],
        portfolio_id=portfolio_id, 
        errors=result["errors"]
    )


@router.put("/portfolio/{portfolio_id}/value", response_model=PortfolioUpdateResponse)
async def update_portfolio_value(portfolio_id: str, request: PortfolioValueUpdateRequest,
                               db: Session = Depends(get_db)):
    is_valid, message = validate_account_number(request.account_number)
    if not is_valid:
        raise HTTPException(status_code=400, detail=message)
    
    service = PortfolioService(db)
    result = service.update_portfolio_value(
        portfolio_id, request.account_number, Decimal(str(request.total_value)), request.user
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return PortfolioUpdateResponse(
        success=result["success"],
        message=result["message"],
        portfolio_id=portfolio_id,
        errors=result["errors"]
    )
