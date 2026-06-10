import pytest
from decimal import Decimal
from datetime import date, time, datetime

from models.transactions import Transaction


class TestTransactionValidation:

    def _make_buy(self, **overrides):
        defaults = dict(
            date=date.today(), time=time(9, 30), portfolio_id="PORT1234",
            sequence_no="000001", investment_id="AAPL123456", type="BU",
            quantity=Decimal("100"), price=Decimal("150.00"), status="P",
        )
        defaults.update(overrides)
        return Transaction(**defaults)

    def test_valid_buy_transaction(self):
        t = self._make_buy()
        result = t.validate_transaction()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_valid_sell_transaction(self):
        t = self._make_buy(type="SL")
        result = t.validate_transaction()
        assert result["valid"] is True

    def test_valid_fee_transaction_no_investment_id(self):
        t = self._make_buy(type="FE", investment_id=None, quantity=None, price=None)
        result = t.validate_transaction()
        assert result["valid"] is True

    def test_valid_transfer_transaction(self):
        t = self._make_buy(type="TR", investment_id=None, quantity=None, price=None)
        result = t.validate_transaction()
        assert result["valid"] is True

    def test_invalid_portfolio_id(self):
        t = self._make_buy(portfolio_id="SHORT")
        result = t.validate_transaction()
        assert result["valid"] is False
        assert any("Portfolio ID" in e for e in result["errors"])

    def test_none_portfolio_id(self):
        t = self._make_buy(portfolio_id=None)
        result = t.validate_transaction()
        assert result["valid"] is False

    def test_invalid_sequence_no(self):
        t = self._make_buy(sequence_no="001")
        result = t.validate_transaction()
        assert result["valid"] is False
        assert any("Sequence number" in e for e in result["errors"])

    def test_none_sequence_no(self):
        t = self._make_buy(sequence_no=None)
        result = t.validate_transaction()
        assert result["valid"] is False

    def test_invalid_type(self):
        t = self._make_buy(type="XX")
        result = t.validate_transaction()
        assert result["valid"] is False
        assert any("Invalid transaction type" in e for e in result["errors"])

    def test_invalid_status(self):
        t = self._make_buy(status="X")
        result = t.validate_transaction()
        assert result["valid"] is False
        assert any("Invalid status" in e for e in result["errors"])

    def test_buy_requires_investment_id(self):
        t = self._make_buy(investment_id=None)
        result = t.validate_transaction()
        assert result["valid"] is False
        assert any("Investment ID required" in e for e in result["errors"])

    def test_sell_requires_investment_id(self):
        t = self._make_buy(type="SL", investment_id=None)
        result = t.validate_transaction()
        assert result["valid"] is False

    def test_buy_requires_positive_quantity(self):
        t = self._make_buy(quantity=Decimal("0"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert any("Positive quantity" in e for e in result["errors"])

    def test_buy_requires_positive_price(self):
        t = self._make_buy(price=Decimal("0"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert any("Positive price" in e for e in result["errors"])

    def test_buy_negative_quantity(self):
        t = self._make_buy(quantity=Decimal("-10"))
        result = t.validate_transaction()
        assert result["valid"] is False

    def test_buy_none_quantity(self):
        t = self._make_buy(quantity=None)
        result = t.validate_transaction()
        assert result["valid"] is False

    def test_buy_none_price(self):
        t = self._make_buy(price=None)
        result = t.validate_transaction()
        assert result["valid"] is False

    def test_multiple_errors(self):
        t = self._make_buy(portfolio_id="", sequence_no="", type="XX", status="X")
        result = t.validate_transaction()
        assert result["valid"] is False
        assert len(result["errors"]) >= 3

    def test_all_valid_statuses(self):
        for s in ["P", "D", "F", "R"]:
            t = self._make_buy(status=s)
            result = t.validate_transaction()
            assert "Invalid status" not in " ".join(result["errors"])


class TestTransactionStatusTransitions:

    def test_pending_to_done(self):
        t = Transaction(status="P")
        assert t.can_transition_to("D") is True

    def test_pending_to_failed(self):
        t = Transaction(status="P")
        assert t.can_transition_to("F") is True

    def test_done_to_reversed(self):
        t = Transaction(status="D")
        assert t.can_transition_to("R") is True

    def test_failed_to_pending_retry(self):
        t = Transaction(status="F")
        assert t.can_transition_to("P") is True

    def test_reversed_is_terminal(self):
        t = Transaction(status="R")
        assert t.can_transition_to("P") is False
        assert t.can_transition_to("D") is False
        assert t.can_transition_to("F") is False

    def test_pending_cannot_reverse(self):
        t = Transaction(status="P")
        assert t.can_transition_to("R") is False

    def test_done_cannot_go_back_to_pending(self):
        t = Transaction(status="D")
        assert t.can_transition_to("P") is False

    def test_unknown_status(self):
        t = Transaction(status="X")
        assert t.can_transition_to("P") is False


class TestTransactionTransitionStatus:

    def test_successful_transition(self):
        t = Transaction(status="P")
        result = t.transition_status("D", "USER01")
        assert result is True
        assert t.status == "D"
        assert t.process_user == "USER01"
        assert t.process_date is not None

    def test_failed_transition(self):
        t = Transaction(status="R")
        result = t.transition_status("P", "USER01")
        assert result is False
        assert t.status == "R"


class TestTransactionCalculateAmount:

    def test_with_quantity_and_price(self):
        t = Transaction(quantity=Decimal("100"), price=Decimal("150.50"))
        assert t.calculate_transaction_amount() == Decimal("15050.00")

    def test_none_quantity(self):
        t = Transaction(quantity=None, price=Decimal("150.50"))
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_none_price(self):
        t = Transaction(quantity=Decimal("100"), price=None)
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_both_none(self):
        t = Transaction(quantity=None, price=None)
        assert t.calculate_transaction_amount() == Decimal("0.00")


class TestTransactionUpdateAmount:

    def test_update_amount(self):
        t = Transaction(quantity=Decimal("50"), price=Decimal("200"))
        t.update_amount()
        assert t.amount == Decimal("10000")


class TestTransactionToDict:

    def test_to_dict_with_values(self):
        t = Transaction(
            date=date(2024, 6, 1), time=time(9, 30), portfolio_id="PORT1234",
            sequence_no="000001", investment_id="AAPL123456", type="BU",
            quantity=Decimal("100"), price=Decimal("150.00"),
            amount=Decimal("15000.00"), currency="USD", status="P",
            process_date=datetime(2024, 6, 1, 9, 30), process_user="ADMIN"
        )
        d = t.to_dict()
        assert d["date"] == "2024-06-01"
        assert d["time"] == "09:30:00"
        assert d["portfolio_id"] == "PORT1234"
        assert d["sequence_no"] == "000001"
        assert d["type"] == "BU"
        assert d["quantity"] == 100.0
        assert d["price"] == 150.0
        assert d["amount"] == 15000.0
        assert d["currency"] == "USD"
        assert d["status"] == "P"
        assert d["process_user"] == "ADMIN"

    def test_to_dict_with_none_values(self):
        t = Transaction(
            date=None, time=None, portfolio_id="PORT1234",
            sequence_no="000001", type="FE", status="P"
        )
        d = t.to_dict()
        assert d["date"] is None
        assert d["time"] is None
        assert d["quantity"] == 0.0
        assert d["price"] == 0.0
        assert d["amount"] == 0.0
        assert d["process_date"] is None
