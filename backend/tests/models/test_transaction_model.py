import pytest
from decimal import Decimal
from datetime import date, datetime, time
from models.transactions import Transaction


class TestTransactionValidation:

    def test_valid_buy_transaction(self, sample_transaction):
        result = sample_transaction.validate_transaction()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_portfolio_id_none(self):
        t = Transaction(portfolio_id=None, sequence_no="000001", type="BU", status="P",
                        investment_id="AAPL123456", quantity=Decimal("10"), price=Decimal("100"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert any("Portfolio ID" in e for e in result["errors"])

    def test_invalid_portfolio_id_wrong_length(self):
        t = Transaction(portfolio_id="SHORT", sequence_no="000001", type="BU", status="P",
                        investment_id="AAPL123456", quantity=Decimal("10"), price=Decimal("100"))
        result = t.validate_transaction()
        assert result["valid"] is False

    def test_invalid_sequence_no_none(self):
        t = Transaction(portfolio_id="TEST0001", sequence_no=None, type="BU", status="P",
                        investment_id="AAPL123456", quantity=Decimal("10"), price=Decimal("100"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert any("Sequence number" in e for e in result["errors"])

    def test_invalid_sequence_no_wrong_length(self):
        t = Transaction(portfolio_id="TEST0001", sequence_no="001", type="BU", status="P",
                        investment_id="AAPL123456", quantity=Decimal("10"), price=Decimal("100"))
        result = t.validate_transaction()
        assert result["valid"] is False

    @pytest.mark.parametrize("txn_type", ["BU", "SL", "TR", "FE"])
    def test_valid_transaction_types(self, txn_type):
        t = Transaction(portfolio_id="TEST0001", sequence_no="000001", type=txn_type, status="P",
                        investment_id="AAPL123456", quantity=Decimal("10"), price=Decimal("100"))
        result = t.validate_transaction()
        assert result["valid"] is True

    def test_invalid_type(self):
        t = Transaction(portfolio_id="TEST0001", sequence_no="000001", type="XX", status="P")
        result = t.validate_transaction()
        assert result["valid"] is False
        assert any("Invalid transaction type" in e for e in result["errors"])

    @pytest.mark.parametrize("status", ["P", "D", "F", "R"])
    def test_valid_statuses(self, status):
        t = Transaction(portfolio_id="TEST0001", sequence_no="000001", type="FE", status=status)
        result = t.validate_transaction()
        assert result["valid"] is True

    def test_invalid_status(self):
        t = Transaction(portfolio_id="TEST0001", sequence_no="000001", type="FE", status="X")
        result = t.validate_transaction()
        assert result["valid"] is False
        assert any("Invalid status" in e for e in result["errors"])

    def test_buy_requires_investment_id(self):
        t = Transaction(portfolio_id="TEST0001", sequence_no="000001", type="BU", status="P",
                        investment_id=None, quantity=Decimal("10"), price=Decimal("100"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert any("Investment ID required" in e for e in result["errors"])

    def test_sell_requires_investment_id(self):
        t = Transaction(portfolio_id="TEST0001", sequence_no="000001", type="SL", status="P",
                        investment_id=None, quantity=Decimal("10"), price=Decimal("100"))
        result = t.validate_transaction()
        assert result["valid"] is False

    def test_buy_requires_positive_quantity(self):
        t = Transaction(portfolio_id="TEST0001", sequence_no="000001", type="BU", status="P",
                        investment_id="AAPL123456", quantity=Decimal("0"), price=Decimal("100"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert any("Positive quantity" in e for e in result["errors"])

    def test_buy_requires_positive_price(self):
        t = Transaction(portfolio_id="TEST0001", sequence_no="000001", type="BU", status="P",
                        investment_id="AAPL123456", quantity=Decimal("10"), price=Decimal("0"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert any("Positive price" in e for e in result["errors"])

    def test_sell_requires_positive_quantity(self):
        t = Transaction(portfolio_id="TEST0001", sequence_no="000001", type="SL", status="P",
                        investment_id="AAPL123456", quantity=None, price=Decimal("100"))
        result = t.validate_transaction()
        assert result["valid"] is False

    def test_fee_does_not_require_investment_id(self):
        t = Transaction(portfolio_id="TEST0001", sequence_no="000001", type="FE", status="P",
                        investment_id=None, quantity=None, price=None)
        result = t.validate_transaction()
        assert result["valid"] is True

    def test_transfer_does_not_require_investment_id(self):
        t = Transaction(portfolio_id="TEST0001", sequence_no="000001", type="TR", status="P",
                        investment_id=None)
        result = t.validate_transaction()
        assert result["valid"] is True


class TestTransactionStatusTransitions:

    def test_pending_to_done(self):
        t = Transaction(status="P")
        assert t.can_transition_to("D") is True

    def test_pending_to_failed(self):
        t = Transaction(status="P")
        assert t.can_transition_to("F") is True

    def test_pending_to_reversed_invalid(self):
        t = Transaction(status="P")
        assert t.can_transition_to("R") is False

    def test_done_to_reversed(self):
        t = Transaction(status="D")
        assert t.can_transition_to("R") is True

    def test_done_to_pending_invalid(self):
        t = Transaction(status="D")
        assert t.can_transition_to("P") is False

    def test_failed_to_pending_retry(self):
        t = Transaction(status="F")
        assert t.can_transition_to("P") is True

    def test_failed_to_done_invalid(self):
        t = Transaction(status="F")
        assert t.can_transition_to("D") is False

    def test_reversed_is_terminal(self):
        t = Transaction(status="R")
        assert t.can_transition_to("P") is False
        assert t.can_transition_to("D") is False
        assert t.can_transition_to("F") is False

    def test_transition_status_success(self):
        t = Transaction(status="P")
        result = t.transition_status("D", "USER1")
        assert result is True
        assert t.status == "D"
        assert t.process_user == "USER1"
        assert t.process_date is not None

    def test_transition_status_failure(self):
        t = Transaction(status="R")
        result = t.transition_status("P", "USER1")
        assert result is False
        assert t.status == "R"

    def test_unknown_status_transition(self):
        t = Transaction(status="Z")
        assert t.can_transition_to("P") is False


class TestTransactionCalculateAmount:

    def test_calculate_amount(self):
        t = Transaction(quantity=Decimal("100.0000"), price=Decimal("150.0000"))
        assert t.calculate_transaction_amount() == Decimal("15000.0000")

    def test_calculate_amount_none_quantity(self):
        t = Transaction(quantity=None, price=Decimal("150.0000"))
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_calculate_amount_none_price(self):
        t = Transaction(quantity=Decimal("100"), price=None)
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_update_amount(self):
        t = Transaction(quantity=Decimal("50.0000"), price=Decimal("200.0000"))
        t.update_amount()
        assert t.amount == Decimal("10000.0000")


class TestTransactionToDict:

    def test_serialization(self, sample_transaction):
        d = sample_transaction.to_dict()
        assert d["portfolio_id"] == "TEST0001"
        assert d["sequence_no"] == "000001"
        assert d["investment_id"] == "AAPL123456"
        assert d["type"] == "BU"
        assert d["quantity"] == 100.0
        assert d["price"] == 150.0
        assert d["amount"] == 15000.0
        assert d["currency"] == "USD"
        assert d["status"] == "P"
        assert d["date"] == "2024-06-01"

    def test_serialization_none_values(self):
        t = Transaction(
            date=None,
            time=None,
            portfolio_id="TEST0001",
            sequence_no="000001",
            quantity=None,
            price=None,
            amount=None,
            process_date=None,
        )
        d = t.to_dict()
        assert d["date"] is None
        assert d["time"] is None
        assert d["quantity"] == 0.0
        assert d["price"] == 0.0
        assert d["amount"] == 0.0
        assert d["process_date"] is None
