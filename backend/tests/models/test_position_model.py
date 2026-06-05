import pytest
from decimal import Decimal
from datetime import date, datetime
from models.database import Position


class TestPositionCalculateGainLoss:

    def test_positive_gain(self):
        pos = Position(cost_basis=Decimal("10000.00"), market_value=Decimal("12000.00"))
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("2000.00")
        assert result["gain_loss_percent"] == Decimal("20.00")

    def test_negative_loss(self):
        pos = Position(cost_basis=Decimal("10000.00"), market_value=Decimal("8000.00"))
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("-2000.00")
        assert result["gain_loss_percent"] == Decimal("-20.00")

    def test_zero_gain(self):
        pos = Position(cost_basis=Decimal("10000.00"), market_value=Decimal("10000.00"))
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_none_cost_basis_returns_zero(self):
        pos = Position(cost_basis=None, market_value=Decimal("5000.00"))
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_none_market_value_returns_zero(self):
        pos = Position(cost_basis=Decimal("5000.00"), market_value=None)
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_both_none_returns_zero(self):
        pos = Position(cost_basis=None, market_value=None)
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_zero_cost_basis_returns_zero_percent(self):
        pos = Position(cost_basis=Decimal("0.00"), market_value=Decimal("5000.00"))
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")


class TestPositionValidation:

    def test_valid_position(self, sample_position):
        result = sample_position.validate_position()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_portfolio_id_none(self):
        pos = Position(portfolio_id=None, investment_id="AAPL123456", status="A", quantity=Decimal("10"))
        result = pos.validate_position()
        assert result["valid"] is False
        assert any("Portfolio ID" in e for e in result["errors"])

    def test_invalid_portfolio_id_wrong_length(self):
        pos = Position(portfolio_id="SHORT", investment_id="AAPL123456", status="A", quantity=Decimal("10"))
        result = pos.validate_position()
        assert result["valid"] is False

    def test_invalid_investment_id_none(self):
        pos = Position(portfolio_id="TEST0001", investment_id=None, status="A", quantity=Decimal("10"))
        result = pos.validate_position()
        assert result["valid"] is False
        assert any("Investment ID" in e for e in result["errors"])

    def test_invalid_investment_id_wrong_length(self):
        pos = Position(portfolio_id="TEST0001", investment_id="SHORT", status="A", quantity=Decimal("10"))
        result = pos.validate_position()
        assert result["valid"] is False

    def test_invalid_status(self):
        pos = Position(portfolio_id="TEST0001", investment_id="AAPL123456", status="X", quantity=Decimal("10"))
        result = pos.validate_position()
        assert result["valid"] is False
        assert any("status" in e for e in result["errors"])

    def test_negative_quantity(self):
        pos = Position(portfolio_id="TEST0001", investment_id="AAPL123456", status="A", quantity=Decimal("-10"))
        result = pos.validate_position()
        assert result["valid"] is False
        assert any("Quantity" in e for e in result["errors"])

    def test_zero_quantity_valid(self):
        pos = Position(portfolio_id="TEST0001", investment_id="AAPL123456", status="A", quantity=Decimal("0"))
        result = pos.validate_position()
        assert result["valid"] is True

    def test_none_quantity_valid(self):
        pos = Position(portfolio_id="TEST0001", investment_id="AAPL123456", status="A", quantity=None)
        result = pos.validate_position()
        assert result["valid"] is True

    @pytest.mark.parametrize("status", ["A", "C", "P"])
    def test_valid_statuses(self, status):
        pos = Position(portfolio_id="TEST0001", investment_id="AAPL123456", status=status, quantity=Decimal("10"))
        result = pos.validate_position()
        assert result["valid"] is True

    def test_multiple_errors(self):
        pos = Position(portfolio_id=None, investment_id=None, status="X", quantity=Decimal("-10"))
        result = pos.validate_position()
        assert result["valid"] is False
        assert len(result["errors"]) == 4


class TestPositionToDict:

    def test_serialization(self, sample_position):
        d = sample_position.to_dict()
        assert d["portfolio_id"] == "TEST0001"
        assert d["investment_id"] == "AAPL123456"
        assert d["quantity"] == 100.0
        assert d["cost_basis"] == 15000.0
        assert d["market_value"] == 18500.0
        assert d["currency"] == "USD"
        assert d["status"] == "A"
        assert d["gain_loss"] == 3500.0
        assert d["date"] == "2024-06-01"

    def test_serialization_none_values(self):
        pos = Position(
            portfolio_id="TEST0001",
            date=None,
            investment_id="AAPL123456",
            quantity=None,
            cost_basis=None,
            market_value=None,
            last_maint_date=None,
        )
        d = pos.to_dict()
        assert d["quantity"] == 0.0
        assert d["cost_basis"] == 0.0
        assert d["market_value"] == 0.0
        assert d["date"] is None
        assert d["last_maint_date"] is None
