import pytest
from decimal import Decimal
from datetime import date, datetime

from models.database import Position


class TestPositionCreation:
    def test_create_with_valid_fields(self, sample_position):
        assert sample_position.portfolio_id == "PORT0001"
        assert sample_position.date == date(2024, 1, 15)
        assert sample_position.investment_id == "INV-AAPL01"
        assert sample_position.quantity == Decimal("100.0000")
        assert sample_position.cost_basis == Decimal("15000.00")
        assert sample_position.market_value == Decimal("18500.00")
        assert sample_position.currency == "USD"
        assert sample_position.status == "A"
        assert sample_position.last_maint_date == datetime(2024, 6, 1, 10, 30, 0)
        assert sample_position.last_maint_user == "TESTUSER"

    def test_persist_and_retrieve(self, persisted_portfolio_with_position, db_session):
        result = db_session.query(Position).filter_by(portfolio_id="PORT0001").first()
        assert result is not None
        assert result.investment_id == "INV-AAPL01"


class TestValidatePosition:
    def test_valid_position(self, sample_position):
        result = sample_position.validate_position()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_portfolio_id_wrong_length(self):
        pos = Position(portfolio_id="SHORT", investment_id="INV-AAPL01",
                       status="A", quantity=Decimal("10"))
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_portfolio_id_none(self):
        pos = Position(portfolio_id=None, investment_id="INV-AAPL01",
                       status="A", quantity=Decimal("10"))
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_investment_id_wrong_length(self):
        pos = Position(portfolio_id="PORT0001", investment_id="SHORT",
                       status="A", quantity=Decimal("10"))
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Investment ID must be 10 characters" in result["errors"]

    def test_invalid_investment_id_none(self):
        pos = Position(portfolio_id="PORT0001", investment_id=None,
                       status="A", quantity=Decimal("10"))
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Investment ID must be 10 characters" in result["errors"]

    def test_invalid_status(self):
        pos = Position(portfolio_id="PORT0001", investment_id="INV-AAPL01",
                       status="X", quantity=Decimal("10"))
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_negative_quantity(self):
        pos = Position(portfolio_id="PORT0001", investment_id="INV-AAPL01",
                       status="A", quantity=Decimal("-5"))
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Quantity cannot be negative" in result["errors"]

    def test_zero_quantity_is_valid(self):
        pos = Position(portfolio_id="PORT0001", investment_id="INV-AAPL01",
                       status="A", quantity=Decimal("0"))
        result = pos.validate_position()
        assert result["valid"] is True

    def test_multiple_errors(self):
        pos = Position(portfolio_id="BAD", investment_id="BAD",
                       status="Z", quantity=Decimal("-1"))
        result = pos.validate_position()
        assert result["valid"] is False
        assert len(result["errors"]) == 4


class TestCalculateGainLoss:
    def test_profit(self, sample_position):
        result = sample_position.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("3500.00")
        assert result["gain_loss_percent"] > Decimal("0")

    def test_loss(self):
        pos = Position(cost_basis=Decimal("20000.00"), market_value=Decimal("15000.00"))
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("-5000.00")
        assert result["gain_loss_percent"] < Decimal("0")

    def test_zero_cost_basis(self):
        pos = Position(cost_basis=Decimal("0.00"), market_value=Decimal("1000.00"))
        result = pos.calculate_gain_loss()
        # Decimal("0.00") is falsy, so the method short-circuits to zeros
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_none_cost_basis(self):
        pos = Position(cost_basis=None, market_value=Decimal("1000.00"))
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_none_market_value(self):
        pos = Position(cost_basis=Decimal("1000.00"), market_value=None)
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_both_none(self):
        pos = Position(cost_basis=None, market_value=None)
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_breakeven(self):
        pos = Position(cost_basis=Decimal("10000.00"), market_value=Decimal("10000.00"))
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")


class TestPositionToDict:
    def test_serialization(self, sample_position):
        d = sample_position.to_dict()
        assert d["portfolio_id"] == "PORT0001"
        assert d["date"] == "2024-01-15"
        assert d["investment_id"] == "INV-AAPL01"
        assert d["quantity"] == 100.0
        assert d["cost_basis"] == 15000.0
        assert d["market_value"] == 18500.0
        assert d["currency"] == "USD"
        assert d["status"] == "A"
        assert isinstance(d["gain_loss"], float)
        assert isinstance(d["gain_loss_percent"], float)
        assert d["last_maint_date"] is not None
        assert d["last_maint_user"] == "TESTUSER"

    def test_serialization_none_values(self):
        pos = Position(portfolio_id="PORT0001", date=date(2024, 1, 1),
                       investment_id="INV-TEST01")
        d = pos.to_dict()
        assert d["quantity"] == 0.0
        assert d["cost_basis"] == 0.0
        assert d["market_value"] == 0.0
        assert d["date"] == "2024-01-01"
        assert d["last_maint_date"] is None
