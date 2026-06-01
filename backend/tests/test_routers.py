import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.portfolio import (
    PortfolioHolding,
    PortfolioSummary,
    AccountValidationResponse,
    PortfolioValidationResponse,
    ValidationErrorResponse,
    TransactionResponse,
)
from validation.portfolio import validate_account_number


class TestPortfolioHoldingModel:
    """Test the PortfolioHolding pydantic model"""

    def test_create_holding(self):
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
        assert h.name == "Apple Inc."
        assert h.shares == 150
        assert h.currentPrice == 185.25
        assert h.marketValue == 27787.50

    def test_holding_negative_gain_loss(self):
        h = PortfolioHolding(
            symbol="TSLA",
            name="Tesla Inc.",
            shares=50,
            currentPrice=200.0,
            marketValue=10000.0,
            gainLoss=-500.0,
            gainLossPercent=-4.76,
        )
        assert h.gainLoss == -500.0
        assert h.gainLossPercent == -4.76


class TestPortfolioSummaryModel:
    """Test the PortfolioSummary pydantic model"""

    def test_create_summary(self):
        holdings = [
            PortfolioHolding(
                symbol="AAPL", name="Apple Inc.", shares=150,
                currentPrice=185.25, marketValue=27787.50,
                gainLoss=2287.50, gainLossPercent=8.97,
            ),
        ]
        s = PortfolioSummary(
            accountNumber="1234567890",
            totalValue=125750.50,
            totalGainLoss=8250.50,
            totalGainLossPercent=7.02,
            holdings=holdings,
            lastUpdated="March 26, 2024, 02:30 PM",
        )
        assert s.accountNumber == "1234567890"
        assert s.totalValue == 125750.50
        assert len(s.holdings) == 1
        assert s.lastUpdated == "March 26, 2024, 02:30 PM"

    def test_summary_empty_holdings(self):
        s = PortfolioSummary(
            accountNumber="1234567890",
            totalValue=0.0,
            totalGainLoss=0.0,
            totalGainLossPercent=0.0,
            holdings=[],
            lastUpdated="now",
        )
        assert len(s.holdings) == 0


class TestAccountValidationResponse:
    """Test the AccountValidationResponse model"""

    def test_valid_response(self):
        r = AccountValidationResponse(valid=True, message="Valid account number")
        assert r.valid is True
        assert r.message == "Valid account number"

    def test_invalid_response(self):
        r = AccountValidationResponse(valid=False, message="Invalid")
        assert r.valid is False


class TestTransactionResponse:
    """Test the TransactionResponse model"""

    def test_empty_transactions(self):
        r = TransactionResponse(
            accountNumber="1234567890",
            transactions=[],
            message="No transactions found",
        )
        assert r.accountNumber == "1234567890"
        assert r.transactions == []

    def test_with_transactions(self):
        r = TransactionResponse(
            accountNumber="1234567890",
            transactions=[{"id": 1, "type": "BU"}],
            message="Success",
        )
        assert len(r.transactions) == 1


class TestValidateAccountNumberIntegration:
    """Test the validate_account_number function used by routers"""

    def test_currently_bypassed(self):
        """The account validation is currently disabled (IDOR vulnerability)"""
        valid, message = validate_account_number("anything")
        assert valid is True
        assert message == "Validation bypassed"

    def test_bypassed_for_empty_string(self):
        valid, message = validate_account_number("")
        assert valid is True

    def test_bypassed_for_none(self):
        valid, message = validate_account_number(None)
        assert valid is True
