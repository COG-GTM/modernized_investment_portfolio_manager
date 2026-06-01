import pytest
from decimal import Decimal
from datetime import date, datetime
from models.database import Portfolio, Position


class TestPortfolioValidation:
    """Test Portfolio.validate_portfolio method."""

    def test_valid_portfolio(self):
        p = Portfolio(port_id="TEST0001", account_no="1234567890", client_type="I", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_port_id_length(self):
        p = Portfolio(port_id="SHORT", account_no="1234567890", client_type="I", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_empty_port_id(self):
        p = Portfolio(port_id="", account_no="1234567890", client_type="I", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is False

    def test_none_port_id(self):
        p = Portfolio(port_id=None, account_no="1234567890", client_type="I", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is False

    def test_invalid_account_no_length(self):
        p = Portfolio(port_id="TEST0001", account_no="12345", client_type="I", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Account number must be 10 characters" in result["errors"]

    def test_invalid_client_type(self):
        p = Portfolio(port_id="TEST0001", account_no="1234567890", client_type="X", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Invalid client type" in result["errors"]

    def test_valid_client_types(self):
        for ct in ["I", "C", "T"]:
            p = Portfolio(port_id="TEST0001", account_no="1234567890", client_type=ct, status="A")
            result = p.validate_portfolio()
            assert result["valid"] is True

    def test_invalid_status(self):
        p = Portfolio(port_id="TEST0001", account_no="1234567890", client_type="I", status="X")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_valid_statuses(self):
        for s in ["A", "C", "S"]:
            p = Portfolio(port_id="TEST0001", account_no="1234567890", client_type="I", status=s)
            result = p.validate_portfolio()
            assert result["valid"] is True

    def test_multiple_errors(self):
        p = Portfolio(port_id="", account_no="", client_type="X", status="X")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert len(result["errors"]) >= 3


class TestPortfolioCalculateTotalValue:
    """Test Portfolio.calculate_total_value method."""

    def test_empty_positions_with_cash(self, db_session):
        p = Portfolio(
            port_id="TEST0001", account_no="1234567890", client_type="I",
            status="A", cash_balance=Decimal("5000.00"),
        )
        db_session.add(p)
        db_session.flush()
        assert p.calculate_total_value() == Decimal("5000.00")

    def test_none_cash_balance(self, db_session):
        p = Portfolio(
            port_id="TEST0002", account_no="1234567891", client_type="I",
            status="A", cash_balance=None,
        )
        db_session.add(p)
        db_session.flush()
        assert p.calculate_total_value() == Decimal("0.00")

    def test_with_active_positions(self, db_session):
        p = Portfolio(
            port_id="TEST0003", account_no="1234567892", client_type="I",
            status="A", cash_balance=Decimal("1000.00"),
        )
        db_session.add(p)
        db_session.flush()

        pos = Position(
            portfolio_id="TEST0003", date=date.today(), investment_id="AAPL123456",
            market_value=Decimal("5000.00"), status="A",
        )
        db_session.add(pos)
        db_session.flush()

        total = p.calculate_total_value()
        assert total == Decimal("6000.00")

    def test_skips_inactive_positions(self, db_session):
        p = Portfolio(
            port_id="TEST0004", account_no="1234567893", client_type="I",
            status="A", cash_balance=Decimal("1000.00"),
        )
        db_session.add(p)
        db_session.flush()

        pos = Position(
            portfolio_id="TEST0004", date=date.today(), investment_id="AAPL123456",
            market_value=Decimal("5000.00"), status="C",
        )
        db_session.add(pos)
        db_session.flush()

        total = p.calculate_total_value()
        assert total == Decimal("1000.00")


class TestPortfolioUpdateTotalValue:
    """Test Portfolio.update_total_value method."""

    def test_updates_total_value_and_date(self, db_session):
        p = Portfolio(
            port_id="TEST0005", account_no="1234567894", client_type="I",
            status="A", cash_balance=Decimal("3000.00"),
        )
        db_session.add(p)
        db_session.flush()

        p.update_total_value()
        assert p.total_value == Decimal("3000.00")
        assert p.last_maint == date.today()


class TestPortfolioToDict:
    """Test Portfolio.to_dict method."""

    def test_serializes_all_fields(self):
        p = Portfolio(
            port_id="TEST0006", account_no="1234567895", client_name="John Doe",
            client_type="I", create_date=date(2024, 1, 15), last_maint=date(2024, 6, 1),
            status="A", total_value=Decimal("50000.00"), cash_balance=Decimal("10000.00"),
            last_user="ADMIN", last_trans="TR000001",
        )
        d = p.to_dict()
        assert d["port_id"] == "TEST0006"
        assert d["account_no"] == "1234567895"
        assert d["client_name"] == "John Doe"
        assert d["client_type"] == "I"
        assert d["create_date"] == "2024-01-15"
        assert d["last_maint"] == "2024-06-01"
        assert d["status"] == "A"
        assert d["total_value"] == 50000.00
        assert d["cash_balance"] == 10000.00
        assert d["last_user"] == "ADMIN"
        assert d["last_trans"] == "TR000001"

    def test_handles_none_values(self):
        p = Portfolio(port_id="TEST0007", account_no="1234567896")
        d = p.to_dict()
        assert d["create_date"] is None
        assert d["last_maint"] is None
        assert d["total_value"] == 0.0
        assert d["cash_balance"] == 0.0


class TestPositionCalculateGainLoss:
    """Test Position.calculate_gain_loss method."""

    def test_positive_gain(self):
        pos = Position(cost_basis=Decimal("1000.00"), market_value=Decimal("1500.00"))
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("500.00")
        assert result["gain_loss_percent"] == Decimal("50.00")

    def test_negative_loss(self):
        pos = Position(cost_basis=Decimal("2000.00"), market_value=Decimal("1500.00"))
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("-500.00")

    def test_zero_gain(self):
        pos = Position(cost_basis=Decimal("1000.00"), market_value=Decimal("1000.00"))
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")

    def test_none_cost_basis(self):
        pos = Position(cost_basis=None, market_value=Decimal("1000.00"))
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_none_market_value(self):
        pos = Position(cost_basis=Decimal("1000.00"), market_value=None)
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")

    def test_zero_cost_basis(self):
        pos = Position(cost_basis=Decimal("0.00"), market_value=Decimal("100.00"))
        result = pos.calculate_gain_loss()
        assert result["gain_loss_percent"] == Decimal("0.00")


class TestPositionValidation:
    """Test Position.validate_position method."""

    def test_valid_position(self):
        pos = Position(
            portfolio_id="TEST0001", investment_id="AAPL123456",
            status="A", quantity=Decimal("100"),
        )
        result = pos.validate_position()
        assert result["valid"] is True

    def test_invalid_portfolio_id(self):
        pos = Position(
            portfolio_id="SHORT", investment_id="AAPL123456",
            status="A", quantity=Decimal("100"),
        )
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_investment_id(self):
        pos = Position(
            portfolio_id="TEST0001", investment_id="SHORT",
            status="A", quantity=Decimal("100"),
        )
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Investment ID must be 10 characters" in result["errors"]

    def test_invalid_status(self):
        pos = Position(
            portfolio_id="TEST0001", investment_id="AAPL123456",
            status="X", quantity=Decimal("100"),
        )
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_valid_statuses(self):
        for s in ["A", "C", "P"]:
            pos = Position(
                portfolio_id="TEST0001", investment_id="AAPL123456",
                status=s, quantity=Decimal("100"),
            )
            result = pos.validate_position()
            assert result["valid"] is True

    def test_negative_quantity(self):
        pos = Position(
            portfolio_id="TEST0001", investment_id="AAPL123456",
            status="A", quantity=Decimal("-10"),
        )
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Quantity cannot be negative" in result["errors"]

    def test_zero_quantity_is_valid(self):
        pos = Position(
            portfolio_id="TEST0001", investment_id="AAPL123456",
            status="A", quantity=Decimal("0"),
        )
        result = pos.validate_position()
        assert result["valid"] is True


class TestPositionToDict:
    """Test Position.to_dict method."""

    def test_serializes_all_fields(self):
        pos = Position(
            portfolio_id="TEST0001", date=date(2024, 6, 15),
            investment_id="AAPL123456", quantity=Decimal("100.0000"),
            cost_basis=Decimal("15000.00"), market_value=Decimal("18500.00"),
            currency="USD", status="A",
            last_maint_date=datetime(2024, 6, 15, 10, 30),
            last_maint_user="ADMIN",
        )
        d = pos.to_dict()
        assert d["portfolio_id"] == "TEST0001"
        assert d["date"] == "2024-06-15"
        assert d["investment_id"] == "AAPL123456"
        assert d["quantity"] == 100.0
        assert d["cost_basis"] == 15000.00
        assert d["market_value"] == 18500.00
        assert d["currency"] == "USD"
        assert d["status"] == "A"
        assert d["gain_loss"] == 3500.00
        assert d["last_maint_user"] == "ADMIN"

    def test_handles_none_values(self):
        pos = Position(portfolio_id="TEST0001", investment_id="AAPL123456")
        d = pos.to_dict()
        assert d["date"] is None
        assert d["quantity"] == 0.0
        assert d["cost_basis"] == 0.0
        assert d["market_value"] == 0.0
        assert d["last_maint_date"] is None
