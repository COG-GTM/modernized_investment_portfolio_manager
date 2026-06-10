import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
class TestGetPortfolio:

    async def test_returns_portfolio_for_valid_account(self, client):
        async with client as c:
            resp = await c.get("/api/portfolio/1234567890")
        assert resp.status_code == 200
        data = resp.json()
        assert data["accountNumber"] == "1234567890"
        assert "totalValue" in data
        assert "holdings" in data
        assert len(data["holdings"]) == 4

    async def test_returns_holdings_with_correct_fields(self, client):
        async with client as c:
            resp = await c.get("/api/portfolio/1234567890")
        holding = resp.json()["holdings"][0]
        assert "symbol" in holding
        assert "name" in holding
        assert "shares" in holding
        assert "currentPrice" in holding
        assert "marketValue" in holding
        assert "gainLoss" in holding
        assert "gainLossPercent" in holding

    async def test_works_with_any_account_number_idor(self, client):
        async with client as c:
            resp = await c.get("/api/portfolio/anything")
        assert resp.status_code == 200
        assert resp.json()["accountNumber"] == "anything"

    async def test_portfolio_has_last_updated(self, client):
        async with client as c:
            resp = await c.get("/api/portfolio/1234567890")
        assert "lastUpdated" in resp.json()


@pytest.mark.asyncio
class TestGetTransactions:

    async def test_returns_transactions_placeholder(self, client):
        async with client as c:
            resp = await c.get("/api/transactions/1234567890")
        assert resp.status_code == 200
        data = resp.json()
        assert data["accountNumber"] == "1234567890"
        assert data["transactions"] == []
        assert "message" in data

    async def test_works_with_any_account_idor(self, client):
        async with client as c:
            resp = await c.get("/api/transactions/any-value")
        assert resp.status_code == 200
        assert resp.json()["accountNumber"] == "any-value"
