import pytest
from decimal import Decimal
from datetime import date, datetime

from models.database import Portfolio, Position


class TestPortfolioValidation:

    def test_valid_portfolio(self):
        p = Portfolio(port_id="PORT1234", account_no="1234567890", client_type="I", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_port_id_length(self):
        p = Portfolio(port_id="PORT12", account_no="1234567890", client_type="I", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert any("Portfolio ID must be 8 characters" in e for e in result["errors"])

    def test_empty_port_id(self):
        p = Portfolio(port_id="", account_no="1234567890", client_type="I", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is False

    def test_none_port_id(self):
        p = Portfolio(port_id=None, account_no="1234567890", client_type="I", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is False

    def test_invalid_account_no_length(self):
        p = Portfolio(port_id="PORT1234", account_no="12345", client_type="I", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert any("Account number must be 10 characters" in e for e in result["errors"])

    def test_empty_account_no(self):
        p = Portfolio(port_id="PORT1234", account_no="", client_type="I", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is False

    def test_invalid_client_type(self):
        p = Portfolio(port_id="PORT1234", account_no="1234567890", client_type="X", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert any("Invalid client type" in e for e in result["errors"])

    def test_all_client_types(self):
        for ct in ["I", "C", "T"]:
            p = Portfolio(port_id="PORT1234", account_no="1234567890", client_type=ct, status="A")
            assert p.validate_portfolio()["valid"] is True

    def test_invalid_status(self):
        p = Portfolio(port_id="PORT1234", account_no="1234567890", client_type="I", status="X")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert any("Invalid status" in e for e in result["errors"])

    def test_all_statuses(self):
        for s in ["A", "C", "S"]:
            p = Portfolio(port_id="PORT1234", account_no="1234567890", client_type="I", status=s)
            assert p.validate_portfolio()["valid"] is True

    def test_multiple_errors(self):
        p = Portfolio(port_id="", account_no="", client_type="X", status="X")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert len(result["errors"]) == 4


class TestPortfolioCalculateTotalValue:

    def test_active_positions_summed(self):
        p = Portfolio(port_id="PORT1234", account_no="1234567890", client_type="I", status="A",
                      cash_balance=Decimal("1000.00"))
        pos1 = Position(portfolio_id="PORT1234", investment_id="AAPL123456", status="A",
                        market_value=Decimal("5000.00"), date=date.today())
        pos2 = Position(portfolio_id="PORT1234", investment_id="MSFT123456", status="A",
                        market_value=Decimal("3000.00"), date=date.today())
        p.positions = [pos1, pos2]
        assert p.calculate_total_value() == Decimal("9000.00")

    def test_closed_positions_excluded(self):
        p = Portfolio(port_id="PORT1234", account_no="1234567890", client_type="I", status="A",
                      cash_balance=Decimal("1000.00"))
        pos_active = Position(portfolio_id="PORT1234", investment_id="AAPL123456", status="A",
                              market_value=Decimal("5000.00"), date=date.today())
        pos_closed = Position(portfolio_id="PORT1234", investment_id="MSFT123456", status="C",
                              market_value=Decimal("3000.00"), date=date.today())
        p.positions = [pos_active, pos_closed]
        assert p.calculate_total_value() == Decimal("6000.00")

    def test_pending_positions_excluded(self):
        p = Portfolio(port_id="PORT1234", account_no="1234567890", client_type="I", status="A",
                      cash_balance=Decimal("500.00"))
        pos = Position(portfolio_id="PORT1234", investment_id="AAPL123456", status="P",
                       market_value=Decimal("5000.00"), date=date.today())
        p.positions = [pos]
        assert p.calculate_total_value() == Decimal("500.00")

    def test_none_cash_balance_treated_as_zero(self):
        p = Portfolio(port_id="PORT1234", account_no="1234567890", client_type="I", status="A",
                      cash_balance=None)
        p.positions = []
        assert p.calculate_total_value() == Decimal("0.00")

    def test_none_market_value_treated_as_zero(self):
        p = Portfolio(port_id="PORT1234", account_no="1234567890", client_type="I", status="A",
                      cash_balance=Decimal("1000.00"))
        pos = Position(portfolio_id="PORT1234", investment_id="AAPL123456", status="A",
                       market_value=None, date=date.today())
        p.positions = [pos]
        assert p.calculate_total_value() == Decimal("1000.00")

    def test_no_positions(self):
        p = Portfolio(port_id="PORT1234", account_no="1234567890", client_type="I", status="A",
                      cash_balance=Decimal("2500.00"))
        p.positions = []
        assert p.calculate_total_value() == Decimal("2500.00")


class TestPortfolioUpdateTotalValue:

    def test_updates_total_and_last_maint(self):
        p = Portfolio(port_id="PORT1234", account_no="1234567890", client_type="I", status="A",
                      cash_balance=Decimal("1000.00"))
        p.positions = []
        p.update_total_value()
        assert p.total_value == Decimal("1000.00")
        assert p.last_maint == date.today()


class TestPortfolioToDict:

    def test_to_dict_with_values(self):
        p = Portfolio(
            port_id="PORT1234", account_no="1234567890", client_name="John",
            client_type="I", create_date=date(2024, 1, 1), last_maint=date(2024, 6, 1),
            status="A", total_value=Decimal("50000.00"), cash_balance=Decimal("5000.00"),
            last_user="ADMIN", last_trans="TR001"
        )
        d = p.to_dict()
        assert d["port_id"] == "PORT1234"
        assert d["account_no"] == "1234567890"
        assert d["client_name"] == "John"
        assert d["client_type"] == "I"
        assert d["create_date"] == "2024-01-01"
        assert d["last_maint"] == "2024-06-01"
        assert d["status"] == "A"
        assert d["total_value"] == 50000.0
        assert d["cash_balance"] == 5000.0
        assert d["last_user"] == "ADMIN"
        assert d["last_trans"] == "TR001"

    def test_to_dict_with_none_values(self):
        p = Portfolio(port_id="PORT1234", account_no="1234567890", client_type="I", status="A")
        d = p.to_dict()
        assert d["create_date"] is None
        assert d["last_maint"] is None
        assert d["total_value"] == 0.0
        assert d["cash_balance"] == 0.0


class TestPositionGainLoss:

    def test_positive_gain(self):
        pos = Position(portfolio_id="PORT1234", investment_id="AAPL123456", date=date.today(),
                       cost_basis=Decimal("10000.00"), market_value=Decimal("12000.00"), status="A")
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("2000.00")
        assert result["gain_loss_percent"] == Decimal("20.00")

    def test_negative_gain(self):
        pos = Position(portfolio_id="PORT1234", investment_id="AAPL123456", date=date.today(),
                       cost_basis=Decimal("10000.00"), market_value=Decimal("8000.00"), status="A")
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("-2000.00")

    def test_zero_cost_basis(self):
        pos = Position(portfolio_id="PORT1234", investment_id="AAPL123456", date=date.today(),
                       cost_basis=Decimal("0"), market_value=Decimal("5000.00"), status="A")
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")

    def test_none_cost_basis(self):
        pos = Position(portfolio_id="PORT1234", investment_id="AAPL123456", date=date.today(),
                       cost_basis=None, market_value=Decimal("5000.00"), status="A")
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_none_market_value(self):
        pos = Position(portfolio_id="PORT1234", investment_id="AAPL123456", date=date.today(),
                       cost_basis=Decimal("10000.00"), market_value=None, status="A")
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")


class TestPositionValidation:

    def test_valid_position(self):
        pos = Position(portfolio_id="PORT1234", investment_id="AAPL123456", date=date.today(),
                       quantity=Decimal("100"), status="A")
        result = pos.validate_position()
        assert result["valid"] is True

    def test_invalid_portfolio_id(self):
        pos = Position(portfolio_id="SHORT", investment_id="AAPL123456", date=date.today(),
                       status="A")
        result = pos.validate_position()
        assert result["valid"] is False
        assert any("Portfolio ID" in e for e in result["errors"])

    def test_invalid_investment_id(self):
        pos = Position(portfolio_id="PORT1234", investment_id="SHORT", date=date.today(),
                       status="A")
        result = pos.validate_position()
        assert result["valid"] is False
        assert any("Investment ID" in e for e in result["errors"])

    def test_invalid_status(self):
        pos = Position(portfolio_id="PORT1234", investment_id="AAPL123456", date=date.today(),
                       status="X")
        result = pos.validate_position()
        assert result["valid"] is False
        assert any("Invalid status" in e for e in result["errors"])

    def test_negative_quantity(self):
        pos = Position(portfolio_id="PORT1234", investment_id="AAPL123456", date=date.today(),
                       quantity=Decimal("-10"), status="A")
        result = pos.validate_position()
        assert result["valid"] is False
        assert any("Quantity cannot be negative" in e for e in result["errors"])

    def test_zero_quantity_is_valid(self):
        pos = Position(portfolio_id="PORT1234", investment_id="AAPL123456", date=date.today(),
                       quantity=Decimal("0"), status="A")
        result = pos.validate_position()
        assert result["valid"] is True

    def test_none_portfolio_id(self):
        pos = Position(portfolio_id=None, investment_id="AAPL123456", date=date.today(), status="A")
        result = pos.validate_position()
        assert result["valid"] is False

    def test_none_investment_id(self):
        pos = Position(portfolio_id="PORT1234", investment_id=None, date=date.today(), status="A")
        result = pos.validate_position()
        assert result["valid"] is False


class TestPositionToDict:

    def test_to_dict_with_values(self):
        pos = Position(
            portfolio_id="PORT1234", investment_id="AAPL123456", date=date(2024, 6, 1),
            quantity=Decimal("100.0000"), cost_basis=Decimal("15000.00"),
            market_value=Decimal("18000.00"), currency="USD", status="A",
            last_maint_date=datetime(2024, 6, 1, 12, 0), last_maint_user="ADMIN"
        )
        d = pos.to_dict()
        assert d["portfolio_id"] == "PORT1234"
        assert d["investment_id"] == "AAPL123456"
        assert d["date"] == "2024-06-01"
        assert d["quantity"] == 100.0
        assert d["cost_basis"] == 15000.0
        assert d["market_value"] == 18000.0
        assert d["currency"] == "USD"
        assert d["status"] == "A"
        assert d["gain_loss"] == 3000.0
        assert d["last_maint_user"] == "ADMIN"

    def test_to_dict_with_none_values(self):
        pos = Position(portfolio_id="PORT1234", investment_id="AAPL123456", date=date.today(),
                       status="A")
        d = pos.to_dict()
        assert d["quantity"] == 0.0
        assert d["cost_basis"] == 0.0
        assert d["market_value"] == 0.0
        assert d["last_maint_date"] is None
