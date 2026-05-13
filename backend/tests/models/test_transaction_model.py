import pytest
from decimal import Decimal
from datetime import date, time, datetime

from models.transactions import Transaction


class TestTransactionCreation:
    def test_create_with_valid_fields(self, sample_transaction):
        assert sample_transaction.date == date(2024, 6, 15)
        assert sample_transaction.time == time(9, 30, 0)
        assert sample_transaction.portfolio_id == "PORT0001"
        assert sample_transaction.sequence_no == "000001"
        assert sample_transaction.investment_id == "INV-AAPL01"
        assert sample_transaction.type == "BU"
        assert sample_transaction.quantity == Decimal("50.0000")
        assert sample_transaction.price == Decimal("150.0000")
        assert sample_transaction.amount == Decimal("7500.00")
        assert sample_transaction.currency == "USD"
        assert sample_transaction.status == "P"
        assert sample_transaction.process_date == datetime(2024, 6, 15, 9, 30, 0)
        assert sample_transaction.process_user == "TESTUSER"


class TestValidateTransaction:
    def test_valid_transaction(self, sample_transaction):
        result = sample_transaction.validate_transaction()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_portfolio_id_wrong_length(self):
        txn = Transaction(portfolio_id="SHORT", sequence_no="000001",
                          type="BU", status="P", investment_id="INV-AAPL01",
                          quantity=Decimal("10"), price=Decimal("100"))
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_portfolio_id_none(self):
        txn = Transaction(portfolio_id=None, sequence_no="000001",
                          type="BU", status="P", investment_id="INV-AAPL01",
                          quantity=Decimal("10"), price=Decimal("100"))
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_sequence_no_wrong_length(self):
        txn = Transaction(portfolio_id="PORT0001", sequence_no="01",
                          type="BU", status="P", investment_id="INV-AAPL01",
                          quantity=Decimal("10"), price=Decimal("100"))
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Sequence number must be 6 characters" in result["errors"]

    def test_invalid_sequence_no_none(self):
        txn = Transaction(portfolio_id="PORT0001", sequence_no=None,
                          type="BU", status="P", investment_id="INV-AAPL01",
                          quantity=Decimal("10"), price=Decimal("100"))
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Sequence number must be 6 characters" in result["errors"]

    def test_invalid_type(self):
        txn = Transaction(portfolio_id="PORT0001", sequence_no="000001",
                          type="XX", status="P")
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Invalid transaction type" in result["errors"]

    def test_invalid_status(self):
        txn = Transaction(portfolio_id="PORT0001", sequence_no="000001",
                          type="TR", status="X")
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_buy_missing_investment_id(self):
        txn = Transaction(portfolio_id="PORT0001", sequence_no="000001",
                          type="BU", status="P", investment_id=None,
                          quantity=Decimal("10"), price=Decimal("100"))
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Investment ID required for buy/sell transactions" in result["errors"]

    def test_sell_missing_investment_id(self):
        txn = Transaction(portfolio_id="PORT0001", sequence_no="000001",
                          type="SL", status="P", investment_id=None,
                          quantity=Decimal("10"), price=Decimal("100"))
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Investment ID required for buy/sell transactions" in result["errors"]

    def test_buy_zero_quantity(self):
        txn = Transaction(portfolio_id="PORT0001", sequence_no="000001",
                          type="BU", status="P", investment_id="INV-AAPL01",
                          quantity=Decimal("0"), price=Decimal("100"))
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Positive quantity required for buy/sell transactions" in result["errors"]

    def test_buy_negative_quantity(self):
        txn = Transaction(portfolio_id="PORT0001", sequence_no="000001",
                          type="BU", status="P", investment_id="INV-AAPL01",
                          quantity=Decimal("-5"), price=Decimal("100"))
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Positive quantity required for buy/sell transactions" in result["errors"]

    def test_buy_zero_price(self):
        txn = Transaction(portfolio_id="PORT0001", sequence_no="000001",
                          type="BU", status="P", investment_id="INV-AAPL01",
                          quantity=Decimal("10"), price=Decimal("0"))
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Positive price required for buy/sell transactions" in result["errors"]

    def test_buy_negative_price(self):
        txn = Transaction(portfolio_id="PORT0001", sequence_no="000001",
                          type="BU", status="P", investment_id="INV-AAPL01",
                          quantity=Decimal("10"), price=Decimal("-50"))
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Positive price required for buy/sell transactions" in result["errors"]

    def test_transfer_no_investment_id_ok(self):
        txn = Transaction(portfolio_id="PORT0001", sequence_no="000001",
                          type="TR", status="P")
        result = txn.validate_transaction()
        assert result["valid"] is True

    def test_fee_no_investment_id_ok(self):
        txn = Transaction(portfolio_id="PORT0001", sequence_no="000001",
                          type="FE", status="P")
        result = txn.validate_transaction()
        assert result["valid"] is True

    def test_multiple_errors(self):
        txn = Transaction(portfolio_id="BAD", sequence_no="X",
                          type="XX", status="Z")
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert len(result["errors"]) >= 4


class TestCanTransitionTo:
    def test_pending_to_done(self):
        txn = Transaction(status="P")
        assert txn.can_transition_to("D") is True

    def test_pending_to_failed(self):
        txn = Transaction(status="P")
        assert txn.can_transition_to("F") is True

    def test_done_to_reversed(self):
        txn = Transaction(status="D")
        assert txn.can_transition_to("R") is True

    def test_failed_to_pending(self):
        txn = Transaction(status="F")
        assert txn.can_transition_to("P") is True

    def test_pending_to_reversed_invalid(self):
        txn = Transaction(status="P")
        assert txn.can_transition_to("R") is False

    def test_done_to_pending_invalid(self):
        txn = Transaction(status="D")
        assert txn.can_transition_to("P") is False

    def test_done_to_failed_invalid(self):
        txn = Transaction(status="D")
        assert txn.can_transition_to("F") is False

    def test_reversed_to_any_invalid(self):
        txn = Transaction(status="R")
        assert txn.can_transition_to("P") is False
        assert txn.can_transition_to("D") is False
        assert txn.can_transition_to("F") is False

    def test_failed_to_done_invalid(self):
        txn = Transaction(status="F")
        assert txn.can_transition_to("D") is False


class TestTransitionStatus:
    def test_successful_transition(self):
        txn = Transaction(status="P")
        result = txn.transition_status("D", "ADMIN01")
        assert result is True
        assert txn.status == "D"
        assert txn.process_user == "ADMIN01"
        assert txn.process_date is not None

    def test_invalid_transition(self):
        txn = Transaction(status="R")
        result = txn.transition_status("P", "ADMIN01")
        assert result is False
        assert txn.status == "R"

    def test_transition_updates_process_date(self):
        txn = Transaction(status="P")
        before = datetime.now()
        txn.transition_status("D", "USER01")
        assert txn.process_date >= before


class TestCalculateTransactionAmount:
    def test_with_quantity_and_price(self, sample_transaction):
        result = sample_transaction.calculate_transaction_amount()
        assert result == Decimal("7500.0000")

    def test_with_none_quantity(self):
        txn = Transaction(quantity=None, price=Decimal("100"))
        result = txn.calculate_transaction_amount()
        assert result == Decimal("0.00")

    def test_with_none_price(self):
        txn = Transaction(quantity=Decimal("10"), price=None)
        result = txn.calculate_transaction_amount()
        assert result == Decimal("0.00")

    def test_with_both_none(self):
        txn = Transaction(quantity=None, price=None)
        result = txn.calculate_transaction_amount()
        assert result == Decimal("0.00")


class TestUpdateAmount:
    def test_sets_amount(self):
        txn = Transaction(quantity=Decimal("10"), price=Decimal("25.50"))
        txn.update_amount()
        assert txn.amount == Decimal("255.0000")


class TestTransactionToDict:
    def test_serialization(self, sample_transaction):
        d = sample_transaction.to_dict()
        assert d["date"] == "2024-06-15"
        assert d["time"] == "09:30:00"
        assert d["portfolio_id"] == "PORT0001"
        assert d["sequence_no"] == "000001"
        assert d["investment_id"] == "INV-AAPL01"
        assert d["type"] == "BU"
        assert d["quantity"] == 50.0
        assert d["price"] == 150.0
        assert d["amount"] == 7500.0
        assert d["currency"] == "USD"
        assert d["status"] == "P"
        assert d["process_date"] is not None
        assert d["process_user"] == "TESTUSER"

    def test_serialization_none_values(self):
        txn = Transaction(portfolio_id="PORT0001", sequence_no="000001",
                          type="TR", status="P")
        d = txn.to_dict()
        assert d["date"] is None
        assert d["time"] is None
        assert d["quantity"] == 0.0
        assert d["price"] == 0.0
        assert d["amount"] == 0.0
        assert d["process_date"] is None
