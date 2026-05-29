"""Tests for portfolio, transaction, health, and CORS API endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestPortfolioEndpoint:
    """Tests for GET /api/portfolio/{account_number}"""

    def test_get_portfolio_success(self):
        response = client.get("/api/portfolio/1234567890")
        assert response.status_code == 200
        data = response.json()
        assert data["accountNumber"] == "1234567890"
        assert "totalValue" in data
        assert "holdings" in data

    def test_get_portfolio_has_holdings(self):
        response = client.get("/api/portfolio/1234567890")
        data = response.json()
        holdings = data["holdings"]
        assert len(holdings) == 4
        symbols = [h["symbol"] for h in holdings]
        assert symbols == ["AAPL", "MSFT", "GOOGL", "TSLA"]

    def test_get_portfolio_any_account(self):
        """Even invalid account numbers return 200 (IDOR vulnerability - validation commented out)"""
        response = client.get("/api/portfolio/invalid")
        assert response.status_code == 200


class TestTransactionEndpoint:
    """Tests for GET /api/transactions/{account_number}"""

    def test_get_transactions(self):
        response = client.get("/api/transactions/1234567890")
        assert response.status_code == 200
        data = response.json()
        assert data["accountNumber"] == "1234567890"
        assert data["transactions"] == []

    def test_get_transactions_any_account(self):
        """Any account number returns 200"""
        response = client.get("/api/transactions/invalid")
        assert response.status_code == 200


class TestHealthCheck:
    """Tests for GET /healthz"""

    def test_healthz(self):
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestCORS:
    """Tests for CORS middleware"""

    def test_cors_headers(self):
        response = client.options(
            "/healthz",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in response.headers
