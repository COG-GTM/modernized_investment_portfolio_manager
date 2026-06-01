"""
Tests for Pydantic response models used by the backend routers.
Avoids importing from routers or FastAPI directly due to
pydantic v1/v2 compatibility issues with the installed FastAPI version.
"""
import pytest
from models.portfolio import (
    PortfolioHolding,
    PortfolioSummary,
    AccountValidationResponse,
    PortfolioValidationResponse,
    ValidationErrorResponse,
    TransactionResponse,
)


class TestPydanticModels:
    def test_portfolio_holding_creation(self):
        holding = PortfolioHolding(
            symbol="TEST",
            name="Test Corp",
            shares=100,
            currentPrice=50.0,
            marketValue=5000.0,
            gainLoss=500.0,
            gainLossPercent=10.0,
        )
        assert holding.symbol == "TEST"
        assert holding.shares == 100

    def test_portfolio_summary_creation(self):
        summary = PortfolioSummary(
            accountNumber="1234567890",
            totalValue=10000.0,
            totalGainLoss=1000.0,
            totalGainLossPercent=10.0,
            holdings=[],
            lastUpdated="2024-01-01",
        )
        assert summary.accountNumber == "1234567890"
        assert summary.holdings == []

    def test_account_validation_response(self):
        resp = AccountValidationResponse(valid=True, message="OK")
        assert resp.valid is True
        assert resp.message == "OK"

    def test_portfolio_validation_response(self):
        resp = PortfolioValidationResponse(
            valid=False, message="Invalid field", field="port_id"
        )
        assert resp.valid is False
        assert resp.field == "port_id"

    def test_validation_error_response(self):
        errors = [
            PortfolioValidationResponse(valid=False, message="err1", field="f1"),
            PortfolioValidationResponse(valid=False, message="err2", field="f2"),
        ]
        resp = ValidationErrorResponse(valid=False, errors=errors)
        assert len(resp.errors) == 2

    def test_transaction_response(self):
        resp = TransactionResponse(
            accountNumber="1234567890",
            transactions=[{"id": 1}],
            message="OK",
        )
        assert resp.accountNumber == "1234567890"
        assert len(resp.transactions) == 1
