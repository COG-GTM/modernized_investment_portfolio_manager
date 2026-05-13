import pytest
from decimal import Decimal
from datetime import date, datetime

from models.database import Portfolio, Position


class TestPortfolioCreation:
    def test_valid_creation(self, sample_portfolio):
        assert sample_portfolio.port_id == "PORT0001"
        assert sample_portfolio.account_no == "1234567890"
        assert sample_portfolio.status == "A"

    def test_default_values(self):
        portfolio = Portfolio(port_id="PORT0002", account_no="0000000001")
        assert portfolio.client_name is None
        assert portfolio.client_type is None
        assert portfolio.create_date is None
        assert portfolio.last_maint is None
        assert portfolio.status is None
        assert portfolio.total_value is None
        assert portfolio.cash_balance is None
        assert portfolio.last_user is None
        assert portfolio.last_trans is None

    def test_field_assignments(self):
        portfolio = Portfolio(
            port_id="PORT0003",
            account_no="9876543210",
            client_name="Acme Corp",
            client_type="C",
            create_date=date(2023, 5, 10),
            last_maint=date(2024, 1, 1),
            status="S",
            total_value=Decimal("100000.00"),
            cash_balance=Decimal("25000.00"),
            last_user="USER01",
            last_trans="TR000010",
        )
        assert portfolio.port_id == "PORT0003"
        assert portfolio.account_no == "9876543210"
        assert portfolio.client_name == "Acme Corp"
        assert portfolio.client_type == "C"
        assert portfolio.create_date == date(2023, 5, 10)
        assert portfolio.last_maint == date(2024, 1, 1)
        assert portfolio.status == "S"
        assert portfolio.total_value == Decimal("100000.00")
        assert portfolio.cash_balance == Decimal("25000.00")
        assert portfolio.last_user == "USER01"
        assert portfolio.last_trans == "TR000010"


class TestPortfolioValidation:
    def test_valid_portfolio(self, sample_portfolio):
        result = sample_portfolio.validate_portfolio()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_port_id_wrong_length(self):
        portfolio = Portfolio(
            port_id="SHORT",
            account_no="1234567890",
            client_type="I",
            status="A",
        )
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_account_no(self):
        portfolio = Portfolio(
            port_id="PORT0001",
            account_no="123",
            client_type="I",
            status="A",
        )
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Account number must be 10 characters" in result["errors"]

    def test_invalid_client_type(self):
        portfolio = Portfolio(
            port_id="PORT0001",
            account_no="1234567890",
            client_type="X",
            status="A",
        )
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Invalid client type" in result["errors"]

    def test_invalid_status(self):
        portfolio = Portfolio(
            port_id="PORT0001",
            account_no="1234567890",
            client_type="I",
            status="Z",
        )
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_multiple_errors(self):
        portfolio = Portfolio(
            port_id="X",
            account_no="1",
            client_type="Z",
            status="Q",
        )
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert len(result["errors"]) == 4


class TestPortfolioCalculateTotalValue:
    def test_with_active_positions(self, db_session, sample_portfolio):
        db_session.add(sample_portfolio)
        db_session.flush()

        pos1 = Position(
            portfolio_id="PORT0001",
            date=date(2024, 1, 15),
            investment_id="INV-AAPL01",
            quantity=Decimal("100"),
            market_value=Decimal("18500.00"),
            status="A",
        )
        pos2 = Position(
            portfolio_id="PORT0001",
            date=date(2024, 1, 15),
            investment_id="INV-GOOG01",
            quantity=Decimal("50"),
            market_value=Decimal("12000.00"),
            status="A",
        )
        db_session.add_all([pos1, pos2])
        db_session.flush()

        total = sample_portfolio.calculate_total_value()
        expected = Decimal("18500.00") + Decimal("12000.00") + Decimal("10000.00")
        assert total == expected

    def test_with_mixed_status_positions(self, db_session, sample_portfolio):
        db_session.add(sample_portfolio)
        db_session.flush()

        active = Position(
            portfolio_id="PORT0001",
            date=date(2024, 1, 15),
            investment_id="INV-AAPL01",
            quantity=Decimal("100"),
            market_value=Decimal("18500.00"),
            status="A",
        )
        closed = Position(
            portfolio_id="PORT0001",
            date=date(2024, 1, 15),
            investment_id="INV-GOOG01",
            quantity=Decimal("50"),
            market_value=Decimal("12000.00"),
            status="C",
        )
        db_session.add_all([active, closed])
        db_session.flush()

        total = sample_portfolio.calculate_total_value()
        expected = Decimal("18500.00") + Decimal("10000.00")
        assert total == expected

    def test_with_no_positions(self, db_session, sample_portfolio):
        db_session.add(sample_portfolio)
        db_session.flush()

        total = sample_portfolio.calculate_total_value()
        assert total == Decimal("10000.00")

    def test_with_none_cash_balance(self, db_session):
        portfolio = Portfolio(
            port_id="PORT0002",
            account_no="0000000002",
            client_type="I",
            status="A",
            cash_balance=None,
        )
        db_session.add(portfolio)
        db_session.flush()

        total = portfolio.calculate_total_value()
        assert total == Decimal("0.00")


class TestPortfolioUpdateTotalValue:
    def test_updates_total_value_and_last_maint(self, db_session, sample_portfolio):
        db_session.add(sample_portfolio)
        db_session.flush()

        sample_portfolio.update_total_value()

        assert sample_portfolio.total_value == sample_portfolio.calculate_total_value()
        assert sample_portfolio.last_maint == date.today()


class TestPortfolioToDict:
    def test_all_fields_serialized(self, sample_portfolio):
        d = sample_portfolio.to_dict()
        assert d["port_id"] == "PORT0001"
        assert d["account_no"] == "1234567890"
        assert d["client_name"] == "Test Client"
        assert d["client_type"] == "I"
        assert d["create_date"] == "2024-01-15"
        assert d["last_maint"] == "2024-06-01"
        assert d["status"] == "A"
        assert d["total_value"] == 50000.00
        assert d["cash_balance"] == 10000.00
        assert d["last_user"] == "ADMIN"
        assert d["last_trans"] == "TR000001"

    def test_none_date_handling(self):
        portfolio = Portfolio(
            port_id="PORT0002",
            account_no="0000000002",
            client_type="I",
            status="A",
        )
        d = portfolio.to_dict()
        assert d["create_date"] is None
        assert d["last_maint"] is None
        assert d["total_value"] == 0.0
        assert d["cash_balance"] == 0.0
