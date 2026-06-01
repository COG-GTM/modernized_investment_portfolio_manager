import pytest
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.database import Portfolio, Position


class TestPortfolioValidation:
    """Test Portfolio.validate_portfolio()"""

    def _make_portfolio(self, **overrides):
        defaults = {
            "port_id": "PORT0001",
            "account_no": "1234567890",
            "client_type": "I",
            "status": "A",
        }
        defaults.update(overrides)
        return Portfolio(**defaults)

    def test_valid_portfolio(self):
        p = self._make_portfolio()
        result = p.validate_portfolio()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_port_id_too_short(self):
        p = self._make_portfolio(port_id="PORT")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_port_id_empty(self):
        p = self._make_portfolio(port_id="")
        result = p.validate_portfolio()
        assert result["valid"] is False

    def test_invalid_port_id_none(self):
        p = self._make_portfolio(port_id=None)
        result = p.validate_portfolio()
        assert result["valid"] is False

    def test_invalid_account_no_too_short(self):
        p = self._make_portfolio(account_no="12345")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Account number must be 10 characters" in result["errors"]

    def test_invalid_account_no_none(self):
        p = self._make_portfolio(account_no=None)
        result = p.validate_portfolio()
        assert result["valid"] is False

    def test_invalid_client_type(self):
        p = self._make_portfolio(client_type="X")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Invalid client type" in result["errors"]

    def test_valid_client_types(self):
        for ct in ["I", "C", "T"]:
            p = self._make_portfolio(client_type=ct)
            result = p.validate_portfolio()
            assert result["valid"] is True

    def test_invalid_status(self):
        p = self._make_portfolio(status="X")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_valid_statuses(self):
        for s in ["A", "C", "S"]:
            p = self._make_portfolio(status=s)
            result = p.validate_portfolio()
            assert result["valid"] is True

    def test_multiple_errors(self):
        p = self._make_portfolio(port_id="", account_no="", client_type="X", status="X")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert len(result["errors"]) >= 2


class TestPortfolioCalculations:
    """Test Portfolio calculation methods"""

    def test_calculate_total_value_no_positions(self):
        p = Portfolio(
            port_id="PORT0001",
            account_no="1234567890",
            client_type="I",
            status="A",
            cash_balance=Decimal("5000.00"),
        )
        p.positions = []
        result = p.calculate_total_value()
        assert result == Decimal("5000.00")

    def test_calculate_total_value_with_active_positions(self):
        p = Portfolio(
            port_id="PORT0001",
            account_no="1234567890",
            client_type="I",
            status="A",
            cash_balance=Decimal("1000.00"),
        )
        pos1 = Position(
            portfolio_id="PORT0001",
            investment_id="AAPL123456",
            status="A",
            market_value=Decimal("5000.00"),
        )
        pos2 = Position(
            portfolio_id="PORT0001",
            investment_id="MSFT123456",
            status="A",
            market_value=Decimal("3000.00"),
        )
        p.positions = [pos1, pos2]
        result = p.calculate_total_value()
        assert result == Decimal("9000.00")

    def test_calculate_total_value_excludes_closed_positions(self):
        p = Portfolio(
            port_id="PORT0001",
            account_no="1234567890",
            client_type="I",
            status="A",
            cash_balance=Decimal("1000.00"),
        )
        pos_active = Position(
            portfolio_id="PORT0001",
            investment_id="AAPL123456",
            status="A",
            market_value=Decimal("5000.00"),
        )
        pos_closed = Position(
            portfolio_id="PORT0001",
            investment_id="MSFT123456",
            status="C",
            market_value=Decimal("3000.00"),
        )
        p.positions = [pos_active, pos_closed]
        result = p.calculate_total_value()
        assert result == Decimal("6000.00")

    def test_calculate_total_value_none_cash_balance(self):
        p = Portfolio(
            port_id="PORT0001",
            account_no="1234567890",
            client_type="I",
            status="A",
            cash_balance=None,
        )
        p.positions = []
        result = p.calculate_total_value()
        assert result == Decimal("0.00")

    def test_update_total_value(self):
        p = Portfolio(
            port_id="PORT0001",
            account_no="1234567890",
            client_type="I",
            status="A",
            cash_balance=Decimal("2000.00"),
        )
        p.positions = []
        p.update_total_value()
        assert p.total_value == Decimal("2000.00")
        assert p.last_maint == date.today()


class TestPortfolioToDict:
    """Test Portfolio.to_dict()"""

    def test_to_dict_basic(self):
        p = Portfolio(
            port_id="PORT0001",
            account_no="1234567890",
            client_name="Test Client",
            client_type="I",
            create_date=date(2024, 1, 15),
            last_maint=date(2024, 6, 20),
            status="A",
            total_value=Decimal("50000.00"),
            cash_balance=Decimal("5000.00"),
            last_user="ADMIN01",
            last_trans="TR000001",
        )
        d = p.to_dict()
        assert d["port_id"] == "PORT0001"
        assert d["account_no"] == "1234567890"
        assert d["client_name"] == "Test Client"
        assert d["client_type"] == "I"
        assert d["create_date"] == "2024-01-15"
        assert d["last_maint"] == "2024-06-20"
        assert d["status"] == "A"
        assert d["total_value"] == 50000.0
        assert d["cash_balance"] == 5000.0

    def test_to_dict_none_values(self):
        p = Portfolio(
            port_id="PORT0001",
            account_no="1234567890",
            client_type="I",
            status="A",
            total_value=None,
            cash_balance=None,
            create_date=None,
        )
        d = p.to_dict()
        assert d["total_value"] == 0.0
        assert d["cash_balance"] == 0.0
        assert d["create_date"] is None


class TestPositionValidation:
    """Test Position.validate_position()"""

    def _make_position(self, **overrides):
        defaults = {
            "portfolio_id": "PORT0001",
            "investment_id": "AAPL123456",
            "status": "A",
            "quantity": Decimal("100.0000"),
        }
        defaults.update(overrides)
        return Position(**defaults)

    def test_valid_position(self):
        p = self._make_position()
        result = p.validate_position()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_portfolio_id(self):
        p = self._make_position(portfolio_id="SHORT")
        result = p.validate_position()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_investment_id(self):
        p = self._make_position(investment_id="SHORT")
        result = p.validate_position()
        assert result["valid"] is False
        assert "Investment ID must be 10 characters" in result["errors"]

    def test_invalid_status(self):
        p = self._make_position(status="X")
        result = p.validate_position()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_valid_statuses(self):
        for s in ["A", "C", "P"]:
            p = self._make_position(status=s)
            result = p.validate_position()
            assert result["valid"] is True

    def test_negative_quantity(self):
        p = self._make_position(quantity=Decimal("-10.0000"))
        result = p.validate_position()
        assert result["valid"] is False
        assert "Quantity cannot be negative" in result["errors"]

    def test_zero_quantity_is_valid(self):
        p = self._make_position(quantity=Decimal("0.0000"))
        result = p.validate_position()
        assert result["valid"] is True


class TestPositionCalculations:
    """Test Position.calculate_gain_loss()"""

    def test_gain_loss_positive(self):
        p = Position(
            portfolio_id="PORT0001",
            investment_id="AAPL123456",
            status="A",
            cost_basis=Decimal("10000.00"),
            market_value=Decimal("12000.00"),
        )
        result = p.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("2000.00")
        assert result["gain_loss_percent"] == Decimal("20.00")

    def test_gain_loss_negative(self):
        p = Position(
            portfolio_id="PORT0001",
            investment_id="AAPL123456",
            status="A",
            cost_basis=Decimal("10000.00"),
            market_value=Decimal("8000.00"),
        )
        result = p.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("-2000.00")
        assert result["gain_loss_percent"] == Decimal("-20.00")

    def test_gain_loss_zero(self):
        p = Position(
            portfolio_id="PORT0001",
            investment_id="AAPL123456",
            status="A",
            cost_basis=Decimal("10000.00"),
            market_value=Decimal("10000.00"),
        )
        result = p.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_gain_loss_no_cost_basis(self):
        p = Position(
            portfolio_id="PORT0001",
            investment_id="AAPL123456",
            status="A",
            cost_basis=None,
            market_value=Decimal("5000.00"),
        )
        result = p.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_gain_loss_no_market_value(self):
        p = Position(
            portfolio_id="PORT0001",
            investment_id="AAPL123456",
            status="A",
            cost_basis=Decimal("10000.00"),
            market_value=None,
        )
        result = p.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")


class TestPositionToDict:
    """Test Position.to_dict()"""

    def test_to_dict(self):
        p = Position(
            portfolio_id="PORT0001",
            date=date(2024, 1, 15),
            investment_id="AAPL123456",
            quantity=Decimal("100.0000"),
            cost_basis=Decimal("15000.00"),
            market_value=Decimal("18000.00"),
            currency="USD",
            status="A",
            last_maint_date=datetime(2024, 6, 20, 10, 0, 0),
            last_maint_user="ADMIN01",
        )
        d = p.to_dict()
        assert d["portfolio_id"] == "PORT0001"
        assert d["date"] == "2024-01-15"
        assert d["investment_id"] == "AAPL123456"
        assert d["quantity"] == 100.0
        assert d["cost_basis"] == 15000.0
        assert d["market_value"] == 18000.0
        assert d["currency"] == "USD"
        assert d["status"] == "A"
        assert d["gain_loss"] == 3000.0
        assert d["last_maint_user"] == "ADMIN01"

    def test_to_dict_none_values(self):
        p = Position(
            portfolio_id="PORT0001",
            investment_id="AAPL123456",
            status="A",
            quantity=None,
            cost_basis=None,
            market_value=None,
            date=None,
            last_maint_date=None,
        )
        d = p.to_dict()
        assert d["quantity"] == 0.0
        assert d["cost_basis"] == 0.0
        assert d["market_value"] == 0.0
        assert d["date"] is None
        assert d["last_maint_date"] is None
