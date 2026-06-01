import pytest
from decimal import Decimal
from datetime import date

from models.database import Portfolio, Position


class TestPortfolioCreation:
    def test_create_with_valid_fields(self, sample_portfolio):
        assert sample_portfolio.port_id == "PORT0001"
        assert sample_portfolio.account_no == "1234567890"
        assert sample_portfolio.client_name == "Test Client"
        assert sample_portfolio.client_type == "I"
        assert sample_portfolio.create_date == date(2024, 1, 15)
        assert sample_portfolio.last_maint == date(2024, 6, 1)
        assert sample_portfolio.status == "A"
        assert sample_portfolio.total_value == Decimal("50000.00")
        assert sample_portfolio.cash_balance == Decimal("10000.00")
        assert sample_portfolio.last_user == "TESTUSER"
        assert sample_portfolio.last_trans == "00000001"

    def test_default_values(self):
        portfolio = Portfolio(port_id="PORT0002", account_no="9876543210")
        assert portfolio.client_name is None
        assert portfolio.client_type is None
        assert portfolio.create_date is None
        assert portfolio.last_maint is None
        assert portfolio.status is None
        assert portfolio.total_value is None
        assert portfolio.cash_balance is None
        assert portfolio.last_user is None
        assert portfolio.last_trans is None
        assert portfolio.positions == []

    def test_persist_and_retrieve(self, db_session, sample_portfolio):
        db_session.add(sample_portfolio)
        db_session.flush()
        result = db_session.query(Portfolio).filter_by(port_id="PORT0001").first()
        assert result is not None
        assert result.account_no == "1234567890"


class TestValidatePortfolio:
    def test_valid_portfolio(self, sample_portfolio):
        result = sample_portfolio.validate_portfolio()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_port_id_wrong_length(self):
        portfolio = Portfolio(port_id="SHORT", account_no="1234567890",
                             client_type="I", status="A")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_port_id_none(self):
        portfolio = Portfolio(port_id=None, account_no="1234567890",
                             client_type="I", status="A")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_account_no_wrong_length(self):
        portfolio = Portfolio(port_id="PORT0001", account_no="12345",
                             client_type="I", status="A")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Account number must be 10 characters" in result["errors"]

    def test_invalid_account_no_none(self):
        portfolio = Portfolio(port_id="PORT0001", account_no=None,
                             client_type="I", status="A")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Account number must be 10 characters" in result["errors"]

    def test_invalid_client_type(self):
        portfolio = Portfolio(port_id="PORT0001", account_no="1234567890",
                             client_type="X", status="A")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Invalid client type" in result["errors"]

    def test_invalid_status(self):
        portfolio = Portfolio(port_id="PORT0001", account_no="1234567890",
                             client_type="I", status="X")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_multiple_errors(self):
        portfolio = Portfolio(port_id="BAD", account_no="SHORT",
                             client_type="X", status="Z")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert len(result["errors"]) == 4


class TestPortfolioToDict:
    def test_serialization_all_fields(self, sample_portfolio):
        d = sample_portfolio.to_dict()
        assert d["port_id"] == "PORT0001"
        assert d["account_no"] == "1234567890"
        assert d["client_name"] == "Test Client"
        assert d["client_type"] == "I"
        assert d["create_date"] == "2024-01-15"
        assert d["last_maint"] == "2024-06-01"
        assert d["status"] == "A"
        assert d["total_value"] == 50000.0
        assert d["cash_balance"] == 10000.0
        assert d["last_user"] == "TESTUSER"
        assert d["last_trans"] == "00000001"

    def test_serialization_correct_types(self, sample_portfolio):
        d = sample_portfolio.to_dict()
        assert isinstance(d["port_id"], str)
        assert isinstance(d["total_value"], float)
        assert isinstance(d["cash_balance"], float)
        assert isinstance(d["create_date"], str)

    def test_serialization_none_dates(self):
        portfolio = Portfolio(port_id="PORT0002", account_no="9876543210",
                             total_value=Decimal("100.00"), cash_balance=Decimal("50.00"),
                             client_type="I", status="A")
        d = portfolio.to_dict()
        assert d["create_date"] is None
        assert d["last_maint"] is None

    def test_serialization_zero_values(self):
        portfolio = Portfolio(port_id="PORT0002", account_no="9876543210",
                             client_type="I", status="A")
        d = portfolio.to_dict()
        assert d["total_value"] == 0.0
        assert d["cash_balance"] == 0.0


class TestCalculateTotalValue:
    def test_with_positions_and_cash(self, persisted_portfolio_with_position):
        portfolio = persisted_portfolio_with_position
        total = portfolio.calculate_total_value()
        # position market_value=18500.00 + cash_balance=10000.00
        assert total == Decimal("28500.00")

    def test_with_cash_only(self, sample_portfolio):
        # No positions loaded, just cash balance
        total = sample_portfolio.calculate_total_value()
        assert total == Decimal("10000.00")

    def test_with_no_cash_balance(self):
        portfolio = Portfolio(port_id="PORT0003", account_no="1111111111",
                             cash_balance=None, client_type="I", status="A")
        total = portfolio.calculate_total_value()
        assert total == Decimal("0.00")

    def test_excludes_inactive_positions(self, db_session):
        portfolio = Portfolio(
            port_id="PORT0004", account_no="2222222222",
            client_type="I", status="A", cash_balance=Decimal("1000.00"))
        db_session.add(portfolio)
        db_session.flush()

        active_pos = Position(
            portfolio_id="PORT0004", date=date(2024, 1, 1),
            investment_id="INV-AAPL01", quantity=Decimal("10"),
            market_value=Decimal("500.00"), status="A")
        closed_pos = Position(
            portfolio_id="PORT0004", date=date(2024, 1, 2),
            investment_id="INV-GOOG01", quantity=Decimal("5"),
            market_value=Decimal("300.00"), status="C")
        db_session.add_all([active_pos, closed_pos])
        db_session.flush()

        total = portfolio.calculate_total_value()
        assert total == Decimal("1500.00")


class TestUpdateTotalValue:
    def test_updates_total_and_last_maint(self, persisted_portfolio_with_position):
        portfolio = persisted_portfolio_with_position
        old_maint = portfolio.last_maint
        portfolio.update_total_value()
        assert portfolio.total_value == Decimal("28500.00")
        assert portfolio.last_maint == date.today()
