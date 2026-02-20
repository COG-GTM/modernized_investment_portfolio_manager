from fastapi import APIRouter, HTTPException, Depends
from models.portfolio import (
    PortfolioSummary,
    PortfolioHolding,
    CreatePortfolioRequest,
    CreatePortfolioResponse,
    AddPositionRequest,
    PositionResponse,
    PortfolioPerformanceResponse,
)
from models.database import Portfolio, Position, SessionLocal, Base, engine
from validation.portfolio import validate_account_number
from sqlalchemy.orm import Session
from datetime import datetime, date
from decimal import Decimal
from typing import List, Generator

Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/api", tags=["portfolio"])


def get_db() -> Generator[Session, None, None]:
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


@router.post("/portfolio", response_model=CreatePortfolioResponse, status_code=201)
async def create_portfolio(request: CreatePortfolioRequest, db: Session = Depends(get_db)):
    """Create a new portfolio"""
    portfolio = Portfolio(
        port_id=request.port_id,
        account_no=request.account_no,
        client_name=request.client_name,
        client_type=request.client_type,
        cash_balance=Decimal(str(request.cash_balance)),
        total_value=Decimal(str(request.cash_balance)),
        status="A",
        create_date=date.today(),
        last_maint=date.today(),
    )

    validation = portfolio.validate_portfolio()
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["errors"])

    existing = db.query(Portfolio).filter(
        Portfolio.port_id == request.port_id,
        Portfolio.account_no == request.account_no,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Portfolio already exists")

    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)

    return CreatePortfolioResponse(
        port_id=portfolio.port_id,
        account_no=portfolio.account_no,
        client_name=portfolio.client_name,
        client_type=portfolio.client_type,
        status=portfolio.status,
        cash_balance=float(portfolio.cash_balance) if portfolio.cash_balance else 0.0,
        total_value=float(portfolio.total_value) if portfolio.total_value else 0.0,
        create_date=portfolio.create_date.isoformat() if portfolio.create_date else None,
        last_maint=portfolio.last_maint.isoformat() if portfolio.last_maint else None,
    )


@router.post("/portfolio/{portfolio_id}/positions", response_model=PositionResponse, status_code=201)
async def add_position(portfolio_id: str, request: AddPositionRequest, db: Session = Depends(get_db)):
    """Add a new investment position to a portfolio"""
    portfolio = db.query(Portfolio).filter(Portfolio.port_id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    today = date.today()
    position = Position(
        portfolio_id=portfolio_id,
        date=today,
        investment_id=request.investment_id,
        quantity=Decimal(str(request.quantity)),
        cost_basis=Decimal(str(request.cost_basis)),
        market_value=Decimal(str(request.cost_basis)),
        currency=request.currency,
        status="A",
        last_maint_date=datetime.now(),
    )

    validation = position.validate_position()
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["errors"])

    existing = db.query(Position).filter(
        Position.portfolio_id == portfolio_id,
        Position.date == today,
        Position.investment_id == request.investment_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Position for this investment already exists on this date",
        )

    db.add(position)
    db.commit()
    db.refresh(position)

    gain_loss_data = position.calculate_gain_loss()

    return PositionResponse(
        portfolio_id=position.portfolio_id,
        date=position.date.isoformat() if position.date else None,
        investment_id=position.investment_id,
        quantity=float(position.quantity) if position.quantity else 0.0,
        cost_basis=float(position.cost_basis) if position.cost_basis else 0.0,
        market_value=float(position.market_value) if position.market_value else 0.0,
        currency=position.currency,
        status=position.status,
        gain_loss=float(gain_loss_data["gain_loss"]),
        gain_loss_percent=float(gain_loss_data["gain_loss_percent"]),
    )


@router.get("/portfolio/{portfolio_id}/performance", response_model=PortfolioPerformanceResponse)
async def get_portfolio_performance(portfolio_id: str, db: Session = Depends(get_db)):
    """Calculate and return portfolio performance metrics"""
    portfolio = db.query(Portfolio).filter(Portfolio.port_id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    positions = db.query(Position).filter(Position.portfolio_id == portfolio_id).all()
    active_positions = [p for p in positions if p.status == "A"]

    total_cost_basis = Decimal("0.00")
    total_gain_loss = Decimal("0.00")

    for pos in active_positions:
        total_cost_basis += pos.cost_basis or Decimal("0.00")
        gain_loss_data = pos.calculate_gain_loss()
        total_gain_loss += gain_loss_data["gain_loss"]

    total_value = portfolio.calculate_total_value()

    return PortfolioPerformanceResponse(
        total_value=float(total_value),
        total_cost_basis=float(total_cost_basis),
        total_gain_loss=float(total_gain_loss),
        positions_count=len(positions),
        active_positions=len(active_positions),
        cash_balance=float(portfolio.cash_balance) if portfolio.cash_balance else 0.0,
    )
