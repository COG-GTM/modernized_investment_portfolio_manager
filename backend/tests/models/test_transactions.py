import pytest
from decimal import Decimal
from datetime import date, time, datetime
from models.transactions import Transaction


class TestTransactionValidation:
    """Test Transaction.validate_transaction method."""

    def test_valid_buy_transaction(self):
        t = Transaction(
            portfolio_id="TEST0001", sequence_no="000001",
            type="BU", status="P", investment_id="AAPL123456",
            quantity=Decimal("100"), price=Decimal("150.00"),
        )
        result = t.validate_transaction()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_valid_sell_transaction(self):
        t = Transaction(
            portfolio_id="TEST0001", sequence_no="000001",
            type="SL", status="P", investment_id="AAPL123456",
            quantity=Decimal("50"), price=Decimal("160.00"),
        )
        result = t.validate_transaction()
        assert result["valid"] is True

    def test_valid_transfer_transaction(self):
        t = Transaction(
            portfolio_id="TEST0001", sequence_no="000001",
            type="TR", status="P",
        )
        result = t.validate_transaction()
        assert result["valid"] is True

    def test_valid_fee_transaction(self):
        t = Transaction(
            portfolio_id="TEST0001", sequence_no="000001",
            type="FE", status="P",
        )
        result = t.validate_transaction()
        assert result["valid"] is True

    def test_invalid_portfolio_id(self):
        t = Transaction(
            portfolio_id="SHORT", sequence_no="000001",
            type="BU", status="P", investment_id="AAPL123456",
            quantity=Decimal("100"), price=Decimal("150.00"),
        )
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_sequence_no(self):
        t = Transaction(
            portfolio_id="TEST0001", sequence_no="001",
            type="BU", status="P", investment_id="AAPL123456",
            quantity=Decimal("100"), price=Decimal("150.00"),
        )
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Sequence number must be 6 characters" in result["errors"]

    def test_invalid_type(self):
        t = Transaction(
            portfolio_id="TEST0001", sequence_no="000001",
            type="XX", status="P",
        )
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Invalid transaction type" in result["errors"]

    def test_invalid_status(self):
        t = Transaction(
            portfolio_id="TEST0001", sequence_no="000001",
            type="BU", status="X", investment_id="AAPL123456",
            quantity=Decimal("100"), price=Decimal("150.00"),
        )
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_buy_requires_investment_id(self):
        t = Transaction(
            portfolio_id="TEST0001", sequence_no="000001",
            type="BU", status="P", investment_id=None,
            quantity=Decimal("100"), price=Decimal("150.00"),
        )
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Investment ID required for buy/sell transactions" in result["errors"]

    def test_buy_requires_positive_quantity(self):
        t = Transaction(
            portfolio_id="TEST0001", sequence_no="000001",
            type="BU", status="P", investment_id="AAPL123456",
            quantity=Decimal("0"), price=Decimal("150.00"),
        )
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Positive quantity required for buy/sell transactions" in result["errors"]

    def test_buy_requires_positive_price(self):
        t = Transaction(
            portfolio_id="TEST0001", sequence_no="000001",
            type="BU", status="P", investment_id="AAPL123456",
            quantity=Decimal("100"), price=Decimal("0"),
        )
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Positive price required for buy/sell transactions" in result["errors"]

    def test_multiple_validation_errors(self):
        t = Transaction(
            portfolio_id="", sequence_no="", type="XX", status="X",
        )
        result = t.validate_transaction()
        assert result["valid"] is False
        assert len(result["errors"]) >= 3


class TestTransactionStatusTransitions:
    """Test Transaction status transition methods."""

    def test_can_transition_pending_to_done(self):
        t = Transaction(status="P")
        assert t.can_transition_to("D") is True

    def test_can_transition_pending_to_failed(self):
        t = Transaction(status="P")
        assert t.can_transition_to("F") is True

    def test_cannot_transition_pending_to_reversed(self):
        t = Transaction(status="P")
        assert t.can_transition_to("R") is False

    def test_can_transition_done_to_reversed(self):
        t = Transaction(status="D")
        assert t.can_transition_to("R") is True

    def test_cannot_transition_done_to_pending(self):
        t = Transaction(status="D")
        assert t.can_transition_to("P") is False

    def test_can_transition_failed_to_pending(self):
        t = Transaction(status="F")
        assert t.can_transition_to("P") is True

    def test_reversed_cannot_transition(self):
        t = Transaction(status="R")
        assert t.can_transition_to("P") is False
        assert t.can_transition_to("D") is False
        assert t.can_transition_to("F") is False

    def test_transition_status_success(self):
        t = Transaction(status="P")
        result = t.transition_status("D", "ADMIN")
        assert result is True
        assert t.status == "D"
        assert t.process_user == "ADMIN"
        assert t.process_date is not None

    def test_transition_status_failure(self):
        t = Transaction(status="R")
        result = t.transition_status("P", "ADMIN")
        assert result is False
        assert t.status == "R"

    def test_invalid_current_status(self):
        t = Transaction(status="Z")
        assert t.can_transition_to("P") is False


class TestTransactionCalculations:
    """Test Transaction calculation methods."""

    def test_calculate_transaction_amount(self):
        t = Transaction(quantity=Decimal("100"), price=Decimal("150.25"))
        assert t.calculate_transaction_amount() == Decimal("15025.00")

    def test_calculate_amount_none_quantity(self):
        t = Transaction(quantity=None, price=Decimal("150.00"))
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_calculate_amount_none_price(self):
        t = Transaction(quantity=Decimal("100"), price=None)
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_update_amount(self):
        t = Transaction(quantity=Decimal("10"), price=Decimal("25.50"))
        t.update_amount()
        assert t.amount == Decimal("255.00")


class TestTransactionToDict:
    """Test Transaction.to_dict method."""

    def test_serializes_all_fields(self):
        t = Transaction(
            date=date(2024, 6, 15), time=time(9, 30, 0),
            portfolio_id="TEST0001", sequence_no="000001",
            investment_id="AAPL123456", type="BU",
            quantity=Decimal("100.0000"), price=Decimal("150.2500"),
            amount=Decimal("15025.00"), currency="USD", status="P",
            process_date=datetime(2024, 6, 15, 10, 0, 0),
            process_user="ADMIN",
        )
        d = t.to_dict()
        assert d["date"] == "2024-06-15"
        assert d["time"] == "09:30:00"
        assert d["portfolio_id"] == "TEST0001"
        assert d["sequence_no"] == "000001"
        assert d["investment_id"] == "AAPL123456"
        assert d["type"] == "BU"
        assert d["quantity"] == 100.0
        assert d["price"] == 150.25
        assert d["amount"] == 15025.0
        assert d["currency"] == "USD"
        assert d["status"] == "P"
        assert d["process_user"] == "ADMIN"

    def test_handles_none_values(self):
        t = Transaction(portfolio_id="TEST0001", sequence_no="000001")
        d = t.to_dict()
        assert d["date"] is None
        assert d["time"] is None
        assert d["quantity"] == 0.0
        assert d["price"] == 0.0
        assert d["amount"] == 0.0
        assert d["process_date"] is None
