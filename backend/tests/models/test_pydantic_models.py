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

    def test_create_valid(self):
        h = PortfolioHolding(
            symbol="AAPL",
            name="Apple Inc.",
            shares=150,
            currentPrice=185.25,
            marketValue=27787.50,
            gainLoss=2287.50,
            gainLossPercent=8.97,
        )
        assert h.symbol == "AAPL"
        assert h.shares == 150
        assert h.currentPrice == 185.25

    def test_dict_roundtrip(self):
        h = PortfolioHolding(
            symbol="MSFT", name="Microsoft", shares=100,
            currentPrice=378.85, marketValue=37885.0, gainLoss=3885.0, gainLossPercent=11.42,
        )
        d = h.model_dump()
        assert d["symbol"] == "MSFT"
        assert d["marketValue"] == 37885.0


class TestPortfolioSummary:

    def test_create_valid(self):
        h = PortfolioHolding(
            symbol="AAPL", name="Apple", shares=100,
            currentPrice=150.0, marketValue=15000.0, gainLoss=1000.0, gainLossPercent=7.14,
        )
        s = PortfolioSummary(
            accountNumber="1234567890",
            totalValue=15000.0,
            totalGainLoss=1000.0,
            totalGainLossPercent=7.14,
            holdings=[h],
            lastUpdated="June 1, 2024",
        )
        assert s.accountNumber == "1234567890"
        assert len(s.holdings) == 1


class TestAccountValidationResponse:

    def test_valid_response(self):
        r = AccountValidationResponse(valid=True, message="Valid")
        assert r.valid is True
        assert r.message == "Valid"

    def test_invalid_response(self):
        r = AccountValidationResponse(valid=False, message="Invalid account")
        assert r.valid is False


class TestPortfolioValidationResponse:

    def test_create(self):
        r = PortfolioValidationResponse(valid=False, message="Bad field", field="port_id")
        assert r.field == "port_id"


class TestValidationErrorResponse:

    def test_create_with_errors(self):
        errors = [
            PortfolioValidationResponse(valid=False, message="Bad field", field="port_id"),
            PortfolioValidationResponse(valid=False, message="Bad status", field="status"),
        ]
        r = ValidationErrorResponse(valid=False, errors=errors)
        assert len(r.errors) == 2
        assert r.valid is False


class TestTransactionResponse:

    def test_create(self):
        r = TransactionResponse(
            accountNumber="1234567890",
            transactions=[{"type": "BU"}],
            message="Found 1 transaction",
        )
        assert r.accountNumber == "1234567890"
        assert len(r.transactions) == 1

    def test_empty_transactions(self):
        r = TransactionResponse(
            accountNumber="1234567890",
            transactions=[],
            message="No transactions",
        )
        assert len(r.transactions) == 0
