from models.portfolio import PortfolioHolding, SectorAllocation
from typing import Dict, List

SECTOR_BY_SYMBOL: Dict[str, str] = {
    "AAPL": "Technology",
    "MSFT": "Technology",
    "GOOGL": "Communication Services",
    "TSLA": "Consumer Discretionary",
}

DEFAULT_SECTOR = "Other"


def resolve_sector(symbol: str) -> str:
    """Resolve a holding's symbol to its market sector"""
    return SECTOR_BY_SYMBOL.get(symbol, DEFAULT_SECTOR)


def aggregate_holdings_by_sector(holdings: List[PortfolioHolding]) -> List[SectorAllocation]:
    """Aggregate portfolio holdings by sector.

    Returns one SectorAllocation per sector with total market value,
    percentage allocation of the invested holdings, and number of holdings,
    sorted by market value descending.
    """
    total_market_value = sum(holding.marketValue for holding in holdings)

    sector_values: Dict[str, float] = {}
    sector_counts: Dict[str, int] = {}
    for holding in holdings:
        sector = resolve_sector(holding.symbol)
        sector_values[sector] = sector_values.get(sector, 0.0) + holding.marketValue
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    allocations = [
        SectorAllocation(
            sector=sector,
            marketValue=round(market_value, 2),
            allocationPercent=round((market_value / total_market_value) * 100, 2)
            if total_market_value
            else 0.0,
            holdingsCount=sector_counts[sector],
        )
        for sector, market_value in sector_values.items()
    ]

    allocations.sort(key=lambda allocation: allocation.marketValue, reverse=True)
    return allocations
