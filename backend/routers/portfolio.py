from fastapi import APIRouter, HTTPException
from models.portfolio import (
    PortfolioSummary, PortfolioHolding, PortfolioAnalytics,
    PerformanceMetrics, AssetAllocation, RiskScores, PieChartData,
    LineGraphPoint, TransactionItem, TransactionFilterResponse,
    CompareRequest, PortfolioComparisonItem, PortfolioComparisonResponse,
)
from validation.portfolio import validate_account_number
from datetime import datetime, date, timedelta
from typing import List, Optional
import random
import math

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
    # Removed account validation - IDOR vulnerability
    # is_valid, message = validate_account_number(account_number)
    # if not is_valid:
    #     raise HTTPException(status_code=400, detail=message)
    
    return generate_mock_portfolio(account_number)


def generate_mock_analytics(account_number: str) -> PortfolioAnalytics:
    """Generate mock analytics data for a portfolio"""
    portfolio = generate_mock_portfolio(account_number)
    total_value = sum(h.marketValue for h in portfolio.holdings)

    asset_allocation = [
        AssetAllocation(
            symbol=h.symbol,
            name=h.name,
            percentage=round(h.marketValue / total_value * 100, 2),
            marketValue=h.marketValue,
        )
        for h in portfolio.holdings
    ]

    pie_chart_data = [
        PieChartData(symbol=a.symbol, percentage=a.percentage)
        for a in asset_allocation
    ]

    base_value = 100000.0
    line_graph_data = []
    for i in range(12):
        d = datetime.now() - timedelta(days=(11 - i) * 30)
        base_value += random.uniform(-2000, 4000)
        line_graph_data.append(
            LineGraphPoint(date=d.strftime("%Y-%m-%d"), value=round(base_value, 2))
        )

    return PortfolioAnalytics(
        accountNumber=account_number,
        performance=PerformanceMetrics(
            totalReturn=8250.50,
            totalReturnPercent=7.02,
            annualizedReturn=12.45,
            volatility=15.32,
            sharpeRatio=1.24,
        ),
        assetAllocation=asset_allocation,
        riskScores=RiskScores(
            overall=6.5,
            market=7.2,
            concentration=5.8,
            volatility=6.1,
        ),
        pieChartData=pie_chart_data,
        lineGraphData=line_graph_data,
        lastUpdated=datetime.now().strftime("%B %d, %Y, %I:%M %p"),
    )


def generate_mock_transactions(account_number: str) -> List[TransactionItem]:
    """Generate mock transaction data"""
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
    transactions = []
    base_date = datetime.now() - timedelta(days=90)
    for i in range(20):
        tx_date = base_date + timedelta(days=i * 4 + random.randint(0, 3))
        symbol = symbols[i % len(symbols)]
        tx_type = "BU" if i % 3 != 0 else "SL"
        qty = round(random.uniform(5, 100), 4)
        price = round(random.uniform(100, 400), 4)
        transactions.append(
            TransactionItem(
                date=tx_date.strftime("%Y-%m-%d"),
                time=tx_date.strftime("%H:%M:%S"),
                portfolioId=account_number[:8].ljust(8, "0"),
                sequenceNo=str(i + 1).zfill(6),
                investmentId=symbol,
                type=tx_type,
                quantity=qty,
                price=price,
                amount=round(qty * price, 2),
                currency="USD",
                status="D",
            )
        )
    return transactions


@router.get("/portfolio/{account_number}/analytics", response_model=PortfolioAnalytics)
async def get_portfolio_analytics(account_number: str):
    """Get portfolio analytics including performance, allocation, risk, and chart data"""
    return generate_mock_analytics(account_number)


@router.get("/transactions/{account_number}", response_model=TransactionFilterResponse)
async def get_transactions(
    account_number: str,
    type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """Get transaction history for an account with optional filtering"""
    transactions = generate_mock_transactions(account_number)

    if type:
        transactions = [t for t in transactions if t.type == type.upper()]
    if start_date:
        transactions = [t for t in transactions if t.date >= start_date.isoformat()]
    if end_date:
        transactions = [t for t in transactions if t.date <= end_date.isoformat()]

    return TransactionFilterResponse(
        accountNumber=account_number,
        transactions=transactions,
        totalCount=len(transactions),
    )


@router.post("/portfolio/compare", response_model=PortfolioComparisonResponse)
async def compare_portfolios(request: CompareRequest):
    """Compare multiple portfolios side by side"""
    if len(request.accountNumbers) < 2:
        raise HTTPException(status_code=400, detail="At least 2 account numbers required")

    portfolios = []
    all_symbols: List[set] = []
    for acct in request.accountNumbers:
        p = generate_mock_portfolio(acct)
        symbols = {h.symbol for h in p.holdings}
        all_symbols.append(symbols)
        top = max(p.holdings, key=lambda h: h.marketValue)
        portfolios.append(
            PortfolioComparisonItem(
                accountNumber=acct,
                totalValue=p.totalValue,
                totalGainLoss=p.totalGainLoss,
                totalGainLossPercent=p.totalGainLossPercent,
                holdingsCount=len(p.holdings),
                topHolding=top.symbol,
            )
        )

    overlap = set.intersection(*all_symbols) if all_symbols else set()
    best = max(portfolios, key=lambda p: p.totalGainLossPercent)
    worst = min(portfolios, key=lambda p: p.totalGainLossPercent)

    return PortfolioComparisonResponse(
        portfolios=portfolios,
        holdingsOverlap=sorted(overlap),
        bestPerformer=best.accountNumber,
        worstPerformer=worst.accountNumber,
    )
