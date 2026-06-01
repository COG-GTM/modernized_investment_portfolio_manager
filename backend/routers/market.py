from fastapi import APIRouter
from models.portfolio import StockQuote
from datetime import datetime
import random

router = APIRouter(prefix="/api", tags=["market"])

BASE_PRICES = {
    "AAPL": 185.25,
    "MSFT": 378.85,
    "GOOGL": 142.56,
    "TSLA": 245.67,
    "AMZN": 178.50,
    "META": 505.75,
    "NVDA": 875.30,
    "JPM": 198.45,
}


@router.get("/market/quote/{symbol}", response_model=StockQuote)
async def get_stock_quote(symbol: str):
    """Get a mock stock quote for a given symbol"""
    symbol_upper = symbol.upper()
    base = BASE_PRICES.get(symbol_upper, 150.00)
    change = round(random.uniform(-base * 0.03, base * 0.03), 2)
    price = round(base + change, 2)
    change_percent = round((change / base) * 100, 2)

    return StockQuote(
        symbol=symbol_upper,
        price=price,
        change=change,
        changePercent=change_percent,
        timestamp=datetime.now().isoformat(),
    )
