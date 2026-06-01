import pytest


class TestGetPortfolio:
    def test_valid_account_returns_200(self, client):
        response = client.get("/api/portfolio/1234567890")
        assert response.status_code == 200
        data = response.json()
        assert data["accountNumber"] == "1234567890"
        assert "totalValue" in data
        assert "holdings" in data
        assert isinstance(data["holdings"], list)
        assert "lastUpdated" in data

    def test_holdings_contain_expected_symbols(self, client):
        response = client.get("/api/portfolio/1234567890")
        data = response.json()
        symbols = [h["symbol"] for h in data["holdings"]]
        for expected in ("AAPL", "MSFT", "GOOGL", "TSLA"):
            assert expected in symbols

    def test_holdings_have_required_fields(self, client):
        response = client.get("/api/portfolio/1234567890")
        data = response.json()
        required_fields = (
            "symbol",
            "name",
            "shares",
            "currentPrice",
            "marketValue",
            "gainLoss",
            "gainLossPercent",
        )
        for holding in data["holdings"]:
            for field in required_fields:
                assert field in holding, f"Missing field '{field}' in holding {holding}"

    def test_any_string_returns_200_due_to_disabled_validation(self, client):
        for account in ("abc", "!@#$%", "anything-goes", ""):
            if account == "":
                continue  # empty string would change the route
            response = client.get(f"/api/portfolio/{account}")
            assert response.status_code == 200


class TestGetTransactions:
    def test_returns_200_with_expected_shape(self, client):
        response = client.get("/api/transactions/1234567890")
        assert response.status_code == 200
        data = response.json()
        assert data["accountNumber"] == "1234567890"
        assert data["transactions"] == []
        assert "message" in data
