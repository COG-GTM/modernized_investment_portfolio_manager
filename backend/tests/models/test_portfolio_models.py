import pytest
from models.portfolio import (
    PortfolioHolding,
    PortfolioSummary,
    AccountValidationResponse,
    PortfolioValidationResponse,
    ValidationErrorResponse,
    TransactionResponse,
)


class TestPortfolioHolding:
    """Test PortfolioHolding Pydantic model."""

    def test_creates_valid_holding(self):
        h = PortfolioHolding(
            symbol="AAPL", name="Apple Inc.", shares=150,
            currentPrice=185.25, marketValue=27787.50,
            gainLoss=2287.50, gainLossPercent=8.97,
        )
        assert h.symbol == "AAPL"
        assert h.name == "Apple Inc."
        assert h.shares == 150
        assert h.currentPrice == 185.25
        assert h.marketValue == 27787.50
        assert h.gainLoss == 2287.50
        assert h.gainLossPercent == 8.97

    def test_serializes_to_dict(self):
        h = PortfolioHolding(
            symbol="MSFT", name="Microsoft", shares=100,
            currentPrice=378.85, marketValue=37885.00,
            gainLoss=3885.00, gainLossPercent=11.42,
        )
        d = h.dict()
        assert d["symbol"] == "MSFT"
        assert d["shares"] == 100

    def test_negative_gain_loss(self):
        h = PortfolioHolding(
            symbol="XYZ", name="XYZ Corp", shares=50,
            currentPrice=10.00, marketValue=500.00,
            gainLoss=-100.00, gainLossPercent=-16.67,
        )
        assert h.gainLoss == -100.00


class TestPortfolioSummary:
    """Test PortfolioSummary Pydantic model."""

    def test_creates_valid_summary(self):
        s = PortfolioSummary(
            accountNumber="1234567890",
            totalValue=125750.50,
            totalGainLoss=8250.50,
            totalGainLossPercent=7.02,
            holdings=[],
            lastUpdated="January 15, 2024",
        )
        assert s.accountNumber == "1234567890"
        assert s.totalValue == 125750.50
        assert s.holdings == []

    def test_with_holdings(self):
        holdings = [
            PortfolioHolding(
                symbol="AAPL", name="Apple", shares=100,
                currentPrice=150.0, marketValue=15000.0,
                gainLoss=500.0, gainLossPercent=3.45,
            ),
        ]
        s = PortfolioSummary(
            accountNumber="1234567890",
            totalValue=15000.0,
            totalGainLoss=500.0,
            totalGainLossPercent=3.45,
            holdings=holdings,
            lastUpdated="2024-01-15",
        )
        assert len(s.holdings) == 1
        assert s.holdings[0].symbol == "AAPL"


class TestAccountValidationResponse:
    """Test AccountValidationResponse Pydantic model."""

    def test_valid_response(self):
        r = AccountValidationResponse(valid=True, message="Valid account number")
        assert r.valid is True
        assert r.message == "Valid account number"

    def test_invalid_response(self):
        r = AccountValidationResponse(valid=False, message="Invalid account")
        assert r.valid is False


class TestPortfolioValidationResponse:
    """Test PortfolioValidationResponse Pydantic model."""

    def test_creates_response(self):
        r = PortfolioValidationResponse(
            valid=False, message="Invalid ID", field="port_id",
        )
        assert r.valid is False
        assert r.field == "port_id"


class TestValidationErrorResponse:
    """Test ValidationErrorResponse Pydantic model."""

    def test_with_errors(self):
        errors = [
            PortfolioValidationResponse(valid=False, message="Bad ID", field="port_id"),
            PortfolioValidationResponse(valid=False, message="Bad status", field="status"),
        ]
        r = ValidationErrorResponse(valid=False, errors=errors)
        assert r.valid is False
        assert len(r.errors) == 2

    def test_empty_errors(self):
        r = ValidationErrorResponse(valid=True, errors=[])
        assert r.valid is True
        assert r.errors == []


class TestTransactionResponse:
    """Test TransactionResponse Pydantic model."""

    def test_creates_response(self):
        r = TransactionResponse(
            accountNumber="1234567890",
            transactions=[{"id": 1, "type": "BU"}],
            message="Success",
        )
        assert r.accountNumber == "1234567890"
        assert len(r.transactions) == 1
        assert r.message == "Success"

    def test_empty_transactions(self):
        r = TransactionResponse(
            accountNumber="1234567890",
            transactions=[],
            message="No transactions",
        )
        assert r.transactions == []
