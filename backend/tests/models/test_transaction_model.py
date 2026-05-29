import pytest
from decimal import Decimal
from datetime import date, datetime, time

from models.transactions import Transaction


class TestTransactionCreation:
    def test_valid_creation(self, sample_transaction):
        assert sample_transaction.portfolio_id == "PORT0001"
        assert sample_transaction.type == "BU"
        assert sample_transaction.status == "P"

    def test_field_assignments(self):
        txn = Transaction(
            date=date(2024, 7, 1),
            time=time(14, 45, 30),
            portfolio_id="PORT0002",
            sequence_no="000010",
            investment_id="INV-GOOG01",
            type="SL",
            quantity=Decimal("50.0000"),
            price=Decimal("2800.0000"),
            amount=Decimal("140000.00"),
            currency="USD",
            status="D",
            process_date=datetime(2024, 7, 1, 14, 45, 30),
            process_user="TRADER02",
        )
        assert txn.date == date(2024, 7, 1)
        assert txn.time == time(14, 45, 30)
        assert txn.portfolio_id == "PORT0002"
        assert txn.sequence_no == "000010"
        assert txn.investment_id == "INV-GOOG01"
        assert txn.type == "SL"
        assert txn.quantity == Decimal("50.0000")
        assert txn.price == Decimal("2800.0000")
        assert txn.amount == Decimal("140000.00")
        assert txn.currency == "USD"
        assert txn.status == "D"
        assert txn.process_date == datetime(2024, 7, 1, 14, 45, 30)
        assert txn.process_user == "TRADER02"


class TestTransactionValidation:
    def test_valid_transaction(self, sample_transaction):
        result = sample_transaction.validate_transaction()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_portfolio_id(self):
        txn = Transaction(
            portfolio_id="ABC",
            sequence_no="000001",
            type="BU",
            status="P",
            investment_id="INV-AAPL01",
            quantity=Decimal("10"),
            price=Decimal("100"),
        )
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_sequence_no(self):
        txn = Transaction(
            portfolio_id="PORT0001",
            sequence_no="01",
            type="BU",
            status="P",
            investment_id="INV-AAPL01",
            quantity=Decimal("10"),
            price=Decimal("100"),
        )
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Sequence number must be 6 characters" in result["errors"]

    def test_invalid_type(self):
        txn = Transaction(
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="XX",
            status="P",
            investment_id="INV-AAPL01",
            quantity=Decimal("10"),
            price=Decimal("100"),
        )
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Invalid transaction type" in result["errors"]

    def test_invalid_status(self):
        txn = Transaction(
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="BU",
            status="Z",
            investment_id="INV-AAPL01",
            quantity=Decimal("10"),
            price=Decimal("100"),
        )
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_missing_investment_id_for_buy_sell(self):
        txn = Transaction(
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="BU",
            status="P",
            investment_id=None,
            quantity=Decimal("10"),
            price=Decimal("100"),
        )
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Investment ID required for buy/sell transactions" in result["errors"]

    def test_zero_quantity_for_buy_sell(self):
        txn = Transaction(
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="SL",
            status="P",
            investment_id="INV-AAPL01",
            quantity=Decimal("0"),
            price=Decimal("100"),
        )
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Positive quantity required for buy/sell transactions" in result["errors"]

    def test_negative_quantity_for_buy_sell(self):
        txn = Transaction(
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="BU",
            status="P",
            investment_id="INV-AAPL01",
            quantity=Decimal("-5"),
            price=Decimal("100"),
        )
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Positive quantity required for buy/sell transactions" in result["errors"]

    def test_zero_price_for_buy_sell(self):
        txn = Transaction(
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="BU",
            status="P",
            investment_id="INV-AAPL01",
            quantity=Decimal("10"),
            price=Decimal("0"),
        )
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Positive price required for buy/sell transactions" in result["errors"]

    def test_negative_price_for_buy_sell(self):
        txn = Transaction(
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="BU",
            status="P",
            investment_id="INV-AAPL01",
            quantity=Decimal("10"),
            price=Decimal("-50"),
        )
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Positive price required for buy/sell transactions" in result["errors"]


class TestTransactionStatusTransitions:
    def test_p_to_d(self):
        txn = Transaction(status="P")
        assert txn.can_transition_to("D") is True

    def test_p_to_f(self):
        txn = Transaction(status="P")
        assert txn.can_transition_to("F") is True

    def test_d_to_r(self):
        txn = Transaction(status="D")
        assert txn.can_transition_to("R") is True

    def test_f_to_p(self):
        txn = Transaction(status="F")
        assert txn.can_transition_to("P") is True

    def test_invalid_d_to_p(self):
        txn = Transaction(status="D")
        assert txn.can_transition_to("P") is False

    def test_invalid_d_to_f(self):
        txn = Transaction(status="D")
        assert txn.can_transition_to("F") is False

    def test_invalid_r_to_d(self):
        txn = Transaction(status="R")
        assert txn.can_transition_to("D") is False

    def test_invalid_r_to_p(self):
        txn = Transaction(status="R")
        assert txn.can_transition_to("P") is False

    def test_invalid_r_to_f(self):
        txn = Transaction(status="R")
        assert txn.can_transition_to("F") is False

    def test_invalid_f_to_d(self):
        txn = Transaction(status="F")
        assert txn.can_transition_to("D") is False

    def test_transition_status_updates_fields(self):
        txn = Transaction(status="P")
        result = txn.transition_status("D", "USER01")
        assert result is True
        assert txn.status == "D"
        assert txn.process_user == "USER01"
        assert txn.process_date is not None

    def test_transition_status_invalid_returns_false(self):
        txn = Transaction(status="R")
        result = txn.transition_status("D", "USER01")
        assert result is False
        assert txn.status == "R"


class TestTransactionAmount:
    def test_calculate_transaction_amount(self):
        txn = Transaction(
            quantity=Decimal("100.0000"),
            price=Decimal("150.5000"),
        )
        amount = txn.calculate_transaction_amount()
        assert amount == Decimal("100.0000") * Decimal("150.5000")

    def test_update_amount(self):
        txn = Transaction(
            quantity=Decimal("50.0000"),
            price=Decimal("200.0000"),
        )
        txn.update_amount()
        assert txn.amount == Decimal("50.0000") * Decimal("200.0000")

    def test_none_values(self):
        txn = Transaction(quantity=None, price=None)
        assert txn.calculate_transaction_amount() == Decimal("0.00")

    def test_none_quantity(self):
        txn = Transaction(quantity=None, price=Decimal("100"))
        assert txn.calculate_transaction_amount() == Decimal("0.00")

    def test_none_price(self):
        txn = Transaction(quantity=Decimal("10"), price=None)
        assert txn.calculate_transaction_amount() == Decimal("0.00")


class TestTransactionToDict:
    def test_all_fields_serialized(self, sample_transaction):
        d = sample_transaction.to_dict()
        assert d["date"] == "2024-06-15"
        assert d["time"] == "09:30:00"
        assert d["portfolio_id"] == "PORT0001"
        assert d["sequence_no"] == "000001"
        assert d["investment_id"] == "INV-AAPL01"
        assert d["type"] == "BU"
        assert d["quantity"] == 100.0
        assert d["price"] == 150.0
        assert d["amount"] == 15000.0
        assert d["currency"] == "USD"
        assert d["status"] == "P"
        assert d["process_date"] == "2024-06-15T09:30:00"
        assert d["process_user"] == "TRADER01"

    def test_none_fields(self):
        txn = Transaction(
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="TR",
            status="P",
        )
        d = txn.to_dict()
        assert d["date"] is None
        assert d["time"] is None
        assert d["quantity"] == 0.0
        assert d["price"] == 0.0
        assert d["amount"] == 0.0
        assert d["process_date"] is None
