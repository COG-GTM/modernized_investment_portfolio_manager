from fastapi.testclient import TestClient
from app.main import app
from models.portfolio import PortfolioHolding
from services.diversification_service import (
    aggregate_holdings_by_sector,
    resolve_sector,
    DEFAULT_SECTOR,
)

client = TestClient(app)


def make_holding(symbol: str, market_value: float) -> PortfolioHolding:
    return PortfolioHolding(
        symbol=symbol,
        name=f"{symbol} Inc.",
        shares=10,
        currentPrice=market_value / 10,
        marketValue=market_value,
        gainLoss=0.0,
        gainLossPercent=0.0,
    )


class TestResolveSector:
    """Test symbol-to-sector resolution"""

    def test_known_symbol(self):
        assert resolve_sector("AAPL") == "Technology"

    def test_communication_services_symbol(self):
        assert resolve_sector("GOOGL") == "Communication Services"

    def test_unknown_symbol_defaults_to_other(self):
        assert resolve_sector("UNKNOWN") == DEFAULT_SECTOR


class TestAggregateHoldingsBySector:
    """Test sector aggregation logic"""

    def test_empty_holdings(self):
        assert aggregate_holdings_by_sector([]) == []

    def test_groups_same_sector_holdings(self):
        holdings = [
            make_holding("AAPL", 6000.0),
            make_holding("MSFT", 4000.0),
        ]
        result = aggregate_holdings_by_sector(holdings)

        assert len(result) == 1
        tech = result[0]
        assert tech.sector == "Technology"
        assert tech.marketValue == 10000.0
        assert tech.holdingsCount == 2
        assert tech.allocationPercent == 100.0

    def test_percentages_across_sectors(self):
        holdings = [
            make_holding("AAPL", 5000.0),
            make_holding("TSLA", 3000.0),
            make_holding("GOOGL", 2000.0),
        ]
        result = aggregate_holdings_by_sector(holdings)

        allocations = {a.sector: a for a in result}
        assert allocations["Technology"].allocationPercent == 50.0
        assert allocations["Consumer Discretionary"].allocationPercent == 30.0
        assert allocations["Communication Services"].allocationPercent == 20.0

    def test_percentages_sum_to_one_hundred(self):
        holdings = [
            make_holding("AAPL", 5000.0),
            make_holding("TSLA", 3000.0),
            make_holding("GOOGL", 2000.0),
        ]
        result = aggregate_holdings_by_sector(holdings)
        assert round(sum(a.allocationPercent for a in result), 2) == 100.0

    def test_sorted_by_market_value_descending(self):
        holdings = [
            make_holding("GOOGL", 2000.0),
            make_holding("AAPL", 5000.0),
            make_holding("TSLA", 3000.0),
        ]
        result = aggregate_holdings_by_sector(holdings)
        market_values = [a.marketValue for a in result]
        assert market_values == sorted(market_values, reverse=True)

    def test_unknown_symbol_bucketed_as_other(self):
        holdings = [make_holding("ZZZZ", 1000.0)]
        result = aggregate_holdings_by_sector(holdings)
        assert result[0].sector == DEFAULT_SECTOR
        assert result[0].holdingsCount == 1


class TestDiversificationEndpoint:
    """Test the diversification API endpoint"""

    def test_returns_diversification_summary(self):
        response = client.get("/api/portfolio/1234567890/diversification")
        assert response.status_code == 200

        data = response.json()
        assert data["accountNumber"] == "1234567890"
        assert "sectors" in data
        assert "totalValue" in data
        assert "lastUpdated" in data

    def test_sectors_have_expected_shape(self):
        response = client.get("/api/portfolio/1234567890/diversification")
        sectors = response.json()["sectors"]

        assert len(sectors) > 0
        for sector in sectors:
            assert set(sector.keys()) == {
                "sector",
                "marketValue",
                "allocationPercent",
                "holdingsCount",
            }

    def test_allocation_percentages_sum_to_one_hundred(self):
        response = client.get("/api/portfolio/1234567890/diversification")
        sectors = response.json()["sectors"]
        total_percent = round(sum(s["allocationPercent"] for s in sectors), 2)
        assert total_percent == 100.0

    def test_total_value_matches_sector_sum(self):
        response = client.get("/api/portfolio/1234567890/diversification")
        data = response.json()
        sector_sum = round(sum(s["marketValue"] for s in data["sectors"]), 2)
        assert sector_sum == round(data["totalValue"], 2)
