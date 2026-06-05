import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestGetPortfolioEndpoint:

    @pytest.mark.asyncio
    async def test_get_portfolio_returns_200(self, client):
        async with client as c:
            response = await c.get("/api/portfolio/1234567890")
        assert response.status_code == 200
        data = response.json()
        assert data["accountNumber"] == "1234567890"
        assert "totalValue" in data
        assert "holdings" in data
        assert "lastUpdated" in data

    @pytest.mark.asyncio
    async def test_get_portfolio_has_four_holdings(self, client):
        async with client as c:
            response = await c.get("/api/portfolio/1234567890")
        data = response.json()
        assert len(data["holdings"]) == 4

    @pytest.mark.asyncio
    async def test_get_portfolio_holding_structure(self, client):
        async with client as c:
            response = await c.get("/api/portfolio/1234567890")
        data = response.json()
        holding = data["holdings"][0]
        assert "symbol" in holding
        assert "name" in holding
        assert "shares" in holding
        assert "currentPrice" in holding
        assert "marketValue" in holding
        assert "gainLoss" in holding
        assert "gainLossPercent" in holding

    @pytest.mark.asyncio
    async def test_get_portfolio_any_account_number(self, client):
        async with client as c:
            response = await c.get("/api/portfolio/9999999999")
        assert response.status_code == 200
        data = response.json()
        assert data["accountNumber"] == "9999999999"

    @pytest.mark.asyncio
    async def test_get_portfolio_total_value(self, client):
        async with client as c:
            response = await c.get("/api/portfolio/1234567890")
        data = response.json()
        assert data["totalValue"] == 125750.50
        assert data["totalGainLoss"] == 8250.50
        assert data["totalGainLossPercent"] == 7.02


class TestGetTransactionsEndpoint:

    @pytest.mark.asyncio
    async def test_get_transactions_returns_200(self, client):
        async with client as c:
            response = await c.get("/api/transactions/1234567890")
        assert response.status_code == 200
        data = response.json()
        assert data["accountNumber"] == "1234567890"
        assert data["transactions"] == []
        assert "message" in data

    @pytest.mark.asyncio
    async def test_get_transactions_any_account(self, client):
        async with client as c:
            response = await c.get("/api/transactions/9999999999")
        assert response.status_code == 200
        data = response.json()
        assert data["accountNumber"] == "9999999999"
