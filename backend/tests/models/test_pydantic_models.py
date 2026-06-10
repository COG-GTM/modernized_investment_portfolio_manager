import pytest
from pydantic import ValidationError

from models.portfolio import (
    PortfolioHolding,
    PortfolioSummary,
    AccountValidationResponse,
    PortfolioValidationResponse,
    ValidationErrorResponse,
    TransactionResponse,
)


class TestPortfolioHolding:

    def test_valid_holding(self):
        h = PortfolioHolding(
            symbol="AAPL", name="Apple Inc.", shares=150,
            currentPrice=185.25, marketValue=27787.50,
            gainLoss=2287.50, gainLossPercent=8.97,
        )
        assert h.symbol == "AAPL"
        assert h.shares == 150

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            PortfolioHolding(symbol="AAPL")


class TestPortfolioSummary:

    def test_valid_summary(self):
        s = PortfolioSummary(
            accountNumber="1234567890",
            totalValue=125000.00,
            totalGainLoss=8250.50,
            totalGainLossPercent=7.02,
            holdings=[
                PortfolioHolding(
                    symbol="AAPL", name="Apple", shares=100,
                    currentPrice=150.0, marketValue=15000.0,
                    gainLoss=500.0, gainLossPercent=3.45,
                )
            ],
            lastUpdated="June 10, 2024",
        )
        assert s.accountNumber == "1234567890"
        assert len(s.holdings) == 1

    def test_empty_holdings(self):
        s = PortfolioSummary(
            accountNumber="1234567890",
            totalValue=0,
            totalGainLoss=0,
            totalGainLossPercent=0,
            holdings=[],
            lastUpdated="now",
        )
        assert s.holdings == []


class TestAccountValidationResponse:

    def test_valid_response(self):
        r = AccountValidationResponse(valid=True, message="ok")
        assert r.valid is True

    def test_invalid_response(self):
        r = AccountValidationResponse(valid=False, message="bad")
        assert r.valid is False


class TestPortfolioValidationResponse:

    def test_valid_response(self):
        r = PortfolioValidationResponse(valid=True, message="ok", field="port_id")
        assert r.field == "port_id"


class TestValidationErrorResponse:

    def test_valid_response(self):
        r = ValidationErrorResponse(
            valid=False,
            errors=[
                PortfolioValidationResponse(valid=False, message="err", field="f")
            ]
        )
        assert len(r.errors) == 1


class TestTransactionResponse:

    def test_valid_response(self):
        r = TransactionResponse(
            accountNumber="1234567890",
            transactions=[{"id": 1}],
            message="ok"
        )
        assert r.accountNumber == "1234567890"

    def test_empty_transactions(self):
        r = TransactionResponse(
            accountNumber="1234567890",
            transactions=[],
            message="none"
        )
        assert r.transactions == []
