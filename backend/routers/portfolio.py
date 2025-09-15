from fastapi import APIRouter, HTTPException, Depends
from models.portfolio import (
    PortfolioSummary, PortfolioHolding, 
    StatusUpdateRequest, ClientNameUpdateRequest, ValueUpdateRequest, PortfolioUpdateResponse
)
from models.database import SessionLocal
from services.portfolio_service import PortfolioService
from validation.portfolio import validate_account_number, validate_portfolio_id
from datetime import datetime
from typing import List

router = APIRouter(prefix="/api", tags=["portfolio"])


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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.put("/portfolio/status", response_model=PortfolioUpdateResponse)
async def update_portfolio_status(request: StatusUpdateRequest, db = Depends(get_db)):
    """Update portfolio status"""
    is_valid_port, port_msg = validate_portfolio_id(request.portfolio_id)
    if not is_valid_port:
        raise HTTPException(status_code=400, detail=port_msg)
    
    is_valid_acct, acct_msg = validate_account_number(request.account_no)
    if not is_valid_acct:
        raise HTTPException(status_code=400, detail=acct_msg)
    
    service = PortfolioService(db)
    result = service.update_portfolio_status(request)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["errors"])
    
    return PortfolioUpdateResponse(
        success=True,
        message="Portfolio status updated successfully",
        portfolio_id=request.portfolio_id
    )


@router.put("/portfolio/client-name", response_model=PortfolioUpdateResponse)
async def update_portfolio_client_name(request: ClientNameUpdateRequest, db = Depends(get_db)):
    """Update portfolio client name"""
    is_valid_port, port_msg = validate_portfolio_id(request.portfolio_id)
    if not is_valid_port:
        raise HTTPException(status_code=400, detail=port_msg)
    
    is_valid_acct, acct_msg = validate_account_number(request.account_no)
    if not is_valid_acct:
        raise HTTPException(status_code=400, detail=acct_msg)
    
    service = PortfolioService(db)
    result = service.update_portfolio_client_name(request)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["errors"])
    
    return PortfolioUpdateResponse(
        success=True,
        message="Portfolio client name updated successfully",
        portfolio_id=request.portfolio_id
    )


@router.put("/portfolio/value", response_model=PortfolioUpdateResponse)
async def update_portfolio_value(request: ValueUpdateRequest, db = Depends(get_db)):
    """Update portfolio total value"""
    is_valid_port, port_msg = validate_portfolio_id(request.portfolio_id)
    if not is_valid_port:
        raise HTTPException(status_code=400, detail=port_msg)
    
    is_valid_acct, acct_msg = validate_account_number(request.account_no)
    if not is_valid_acct:
        raise HTTPException(status_code=400, detail=acct_msg)
    
    service = PortfolioService(db)
    result = service.update_portfolio_value(request)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["errors"])
    
    return PortfolioUpdateResponse(
        success=True,
        message="Portfolio value updated successfully",
        portfolio_id=request.portfolio_id
    )
