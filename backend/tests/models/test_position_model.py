import pytest
from decimal import Decimal
from datetime import date, datetime

from models.database import Position


class TestPositionCreation:
    def test_valid_creation(self, sample_position):
        assert sample_position.portfolio_id == "PORT0001"
        assert sample_position.investment_id == "INV-AAPL01"
        assert sample_position.status == "A"

    def test_field_assignments(self):
        position = Position(
            portfolio_id="PORT0002",
            date=date(2024, 3, 20),
            investment_id="INV-MSFT01",
            quantity=Decimal("250.5000"),
            cost_basis=Decimal("80000.00"),
            market_value=Decimal("95000.00"),
            currency="EUR",
            status="P",
            last_maint_date=datetime(2024, 5, 1, 14, 0, 0),
            last_maint_user="TRADER",
        )
        assert position.portfolio_id == "PORT0002"
        assert position.date == date(2024, 3, 20)
        assert position.investment_id == "INV-MSFT01"
        assert position.quantity == Decimal("250.5000")
        assert position.cost_basis == Decimal("80000.00")
        assert position.market_value == Decimal("95000.00")
        assert position.currency == "EUR"
        assert position.status == "P"
        assert position.last_maint_date == datetime(2024, 5, 1, 14, 0, 0)
        assert position.last_maint_user == "TRADER"


class TestPositionCalculateGainLoss:
    def test_positive_gain(self):
        position = Position(
            cost_basis=Decimal("10000.00"),
            market_value=Decimal("12000.00"),
        )
        result = position.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("2000.00")
        assert result["gain_loss_percent"] == Decimal("20.00")

    def test_negative_loss(self):
        position = Position(
            cost_basis=Decimal("10000.00"),
            market_value=Decimal("8000.00"),
        )
        result = position.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("-2000.00")
        assert result["gain_loss_percent"] == Decimal("-20.00")

    def test_zero_cost_basis(self):
        position = Position(
            cost_basis=Decimal("0.00"),
            market_value=Decimal("5000.00"),
        )
        result = position.calculate_gain_loss()
        # cost_basis evaluates as falsy, so method returns zero defaults
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_none_values(self):
        position = Position(cost_basis=None, market_value=None)
        result = position.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")


class TestPositionValidation:
    def test_valid_position(self, sample_position):
        result = sample_position.validate_position()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_portfolio_id(self):
        position = Position(
            portfolio_id="ABC",
            investment_id="INV-AAPL01",
            status="A",
            quantity=Decimal("10"),
        )
        result = position.validate_position()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_investment_id(self):
        position = Position(
            portfolio_id="PORT0001",
            investment_id="SHORT",
            status="A",
            quantity=Decimal("10"),
        )
        result = position.validate_position()
        assert result["valid"] is False
        assert "Investment ID must be 10 characters" in result["errors"]

    def test_invalid_status(self):
        position = Position(
            portfolio_id="PORT0001",
            investment_id="INV-AAPL01",
            status="X",
            quantity=Decimal("10"),
        )
        result = position.validate_position()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_negative_quantity(self):
        position = Position(
            portfolio_id="PORT0001",
            investment_id="INV-AAPL01",
            status="A",
            quantity=Decimal("-5"),
        )
        result = position.validate_position()
        assert result["valid"] is False
        assert "Quantity cannot be negative" in result["errors"]


class TestPositionToDict:
    def test_serialization_with_gain_loss_data(self, sample_position):
        d = sample_position.to_dict()
        assert d["portfolio_id"] == "PORT0001"
        assert d["date"] == "2024-01-15"
        assert d["investment_id"] == "INV-AAPL01"
        assert d["quantity"] == 100.0
        assert d["cost_basis"] == 15000.0
        assert d["market_value"] == 18500.0
        assert d["currency"] == "USD"
        assert d["status"] == "A"
        assert d["gain_loss"] == 3500.0
        expected_pct = (3500.0 / 15000.0) * 100
        assert abs(d["gain_loss_percent"] - expected_pct) < 0.01
        assert d["last_maint_date"] == "2024-06-01T10:30:00"
        assert d["last_maint_user"] == "ADMIN"
