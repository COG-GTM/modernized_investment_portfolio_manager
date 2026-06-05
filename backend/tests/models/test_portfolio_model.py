import pytest
from decimal import Decimal
from datetime import date, datetime
from models.database import Portfolio, Position


class TestPortfolioValidation:

    def test_valid_portfolio(self, sample_portfolio):
        result = sample_portfolio.validate_portfolio()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_port_id_none(self):
        p = Portfolio(port_id=None, account_no="1234567890", client_type="I", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert any("Portfolio ID" in e for e in result["errors"])

    def test_invalid_port_id_wrong_length(self):
        p = Portfolio(port_id="SHORT", account_no="1234567890", client_type="I", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is False

    def test_invalid_account_no_none(self):
        p = Portfolio(port_id="TEST0001", account_no=None, client_type="I", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert any("Account number" in e for e in result["errors"])

    def test_invalid_account_no_wrong_length(self):
        p = Portfolio(port_id="TEST0001", account_no="123", client_type="I", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is False

    def test_invalid_client_type(self):
        p = Portfolio(port_id="TEST0001", account_no="1234567890", client_type="X", status="A")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert any("client type" in e for e in result["errors"])

    def test_invalid_status(self):
        p = Portfolio(port_id="TEST0001", account_no="1234567890", client_type="I", status="X")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert any("status" in e for e in result["errors"])

    def test_multiple_errors(self):
        p = Portfolio(port_id=None, account_no=None, client_type="X", status="X")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert len(result["errors"]) == 4

    @pytest.mark.parametrize("client_type", ["I", "C", "T"])
    def test_valid_client_types(self, client_type):
        p = Portfolio(port_id="TEST0001", account_no="1234567890", client_type=client_type, status="A")
        result = p.validate_portfolio()
        assert result["valid"] is True

    @pytest.mark.parametrize("status", ["A", "C", "S"])
    def test_valid_statuses(self, status):
        p = Portfolio(port_id="TEST0001", account_no="1234567890", client_type="I", status=status)
        result = p.validate_portfolio()
        assert result["valid"] is True


class TestPortfolioCalculateTotalValue:

    def test_with_active_positions_and_cash(self):
        p = Portfolio(cash_balance=Decimal("1000.00"))
        pos1 = Position(status="A", market_value=Decimal("5000.00"))
        pos2 = Position(status="A", market_value=Decimal("3000.00"))
        p.positions = [pos1, pos2]
        assert p.calculate_total_value() == Decimal("9000.00")

    def test_excludes_closed_positions(self):
        p = Portfolio(cash_balance=Decimal("1000.00"))
        pos1 = Position(status="A", market_value=Decimal("5000.00"))
        pos2 = Position(status="C", market_value=Decimal("3000.00"))
        p.positions = [pos1, pos2]
        assert p.calculate_total_value() == Decimal("6000.00")

    def test_excludes_pending_positions(self):
        p = Portfolio(cash_balance=Decimal("0.00"))
        pos1 = Position(status="P", market_value=Decimal("5000.00"))
        p.positions = [pos1]
        assert p.calculate_total_value() == Decimal("0.00")

    def test_none_cash_balance_treated_as_zero(self):
        p = Portfolio(cash_balance=None)
        pos1 = Position(status="A", market_value=Decimal("5000.00"))
        p.positions = [pos1]
        assert p.calculate_total_value() == Decimal("5000.00")

    def test_none_market_value_treated_as_zero(self):
        p = Portfolio(cash_balance=Decimal("1000.00"))
        pos1 = Position(status="A", market_value=None)
        p.positions = [pos1]
        assert p.calculate_total_value() == Decimal("1000.00")

    def test_empty_positions(self):
        p = Portfolio(cash_balance=Decimal("500.00"))
        p.positions = []
        assert p.calculate_total_value() == Decimal("500.00")


class TestPortfolioUpdateTotalValue:

    def test_updates_total_and_last_maint(self):
        p = Portfolio(cash_balance=Decimal("100.00"), total_value=Decimal("0.00"))
        p.positions = []
        p.update_total_value()
        assert p.total_value == Decimal("100.00")
        assert p.last_maint == date.today()


class TestPortfolioToDict:

    def test_serialization(self, sample_portfolio):
        d = sample_portfolio.to_dict()
        assert d["port_id"] == "TEST0001"
        assert d["account_no"] == "1234567890"
        assert d["client_name"] == "Test Client"
        assert d["client_type"] == "I"
        assert d["status"] == "A"
        assert d["total_value"] == 100000.0
        assert d["cash_balance"] == 5000.0
        assert d["last_user"] == "TESTUSER"
        assert d["create_date"] == "2024-01-15"
        assert d["last_maint"] == "2024-06-01"

    def test_serialization_none_dates(self):
        p = Portfolio(port_id="TEST0001", account_no="1234567890",
                      create_date=None, last_maint=None, total_value=None, cash_balance=None)
        d = p.to_dict()
        assert d["create_date"] is None
        assert d["last_maint"] is None
        assert d["total_value"] == 0.0
        assert d["cash_balance"] == 0.0
