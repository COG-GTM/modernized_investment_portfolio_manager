import pytest
from decimal import Decimal
from datetime import date, time, datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.transactions import Transaction


class TestTransactionValidation:
    """Test Transaction.validate_transaction()"""

    def _make_transaction(self, **overrides):
        defaults = {
            "date": date(2024, 1, 15),
            "time": time(9, 30, 0),
            "portfolio_id": "PORT0001",
            "sequence_no": "000001",
            "investment_id": "AAPL123456",
            "type": "BU",
            "quantity": Decimal("100.0000"),
            "price": Decimal("150.0000"),
            "amount": Decimal("15000.00"),
            "currency": "USD",
            "status": "P",
        }
        defaults.update(overrides)
        return Transaction(**defaults)

    def test_valid_buy_transaction(self):
        t = self._make_transaction()
        result = t.validate_transaction()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_valid_sell_transaction(self):
        t = self._make_transaction(type="SL")
        result = t.validate_transaction()
        assert result["valid"] is True

    def test_valid_transfer_transaction(self):
        t = self._make_transaction(type="TR")
        result = t.validate_transaction()
        assert result["valid"] is True

    def test_valid_fee_transaction(self):
        t = self._make_transaction(type="FE")
        result = t.validate_transaction()
        assert result["valid"] is True

    def test_invalid_portfolio_id_short(self):
        t = self._make_transaction(portfolio_id="SHORT")
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_portfolio_id_none(self):
        t = self._make_transaction(portfolio_id=None)
        result = t.validate_transaction()
        assert result["valid"] is False

    def test_invalid_sequence_no(self):
        t = self._make_transaction(sequence_no="001")
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Sequence number must be 6 characters" in result["errors"]

    def test_invalid_type(self):
        t = self._make_transaction(type="XX")
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Invalid transaction type" in result["errors"]

    def test_invalid_status(self):
        t = self._make_transaction(status="X")
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_buy_requires_investment_id(self):
        t = self._make_transaction(type="BU", investment_id=None)
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Investment ID required for buy/sell transactions" in result["errors"]

    def test_sell_requires_investment_id(self):
        t = self._make_transaction(type="SL", investment_id=None)
        result = t.validate_transaction()
        assert result["valid"] is False

    def test_buy_requires_positive_quantity(self):
        t = self._make_transaction(type="BU", quantity=Decimal("0"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Positive quantity required for buy/sell transactions" in result["errors"]

    def test_buy_requires_positive_price(self):
        t = self._make_transaction(type="BU", price=Decimal("0"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Positive price required for buy/sell transactions" in result["errors"]

    def test_sell_requires_positive_quantity(self):
        t = self._make_transaction(type="SL", quantity=Decimal("-1"))
        result = t.validate_transaction()
        assert result["valid"] is False

    def test_fee_does_not_require_investment_id(self):
        t = self._make_transaction(type="FE", investment_id=None)
        result = t.validate_transaction()
        # FE type does not require investment_id
        assert "Investment ID required for buy/sell transactions" not in result["errors"]

    def test_multiple_errors(self):
        t = self._make_transaction(
            portfolio_id="",
            sequence_no="",
            type="XX",
            status="X",
        )
        result = t.validate_transaction()
        assert result["valid"] is False
        assert len(result["errors"]) >= 3


class TestTransactionStatusTransitions:
    """Test Transaction.can_transition_to() and transition_status()"""

    def _make_transaction(self, status="P"):
        return Transaction(
            date=date(2024, 1, 15),
            time=time(9, 30, 0),
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="BU",
            status=status,
        )

    def test_pending_can_transition_to_done(self):
        t = self._make_transaction(status="P")
        assert t.can_transition_to("D") is True

    def test_pending_can_transition_to_failed(self):
        t = self._make_transaction(status="P")
        assert t.can_transition_to("F") is True

    def test_pending_cannot_transition_to_reversed(self):
        t = self._make_transaction(status="P")
        assert t.can_transition_to("R") is False

    def test_done_can_transition_to_reversed(self):
        t = self._make_transaction(status="D")
        assert t.can_transition_to("R") is True

    def test_done_cannot_transition_to_pending(self):
        t = self._make_transaction(status="D")
        assert t.can_transition_to("P") is False

    def test_failed_can_transition_to_pending(self):
        t = self._make_transaction(status="F")
        assert t.can_transition_to("P") is True

    def test_reversed_cannot_transition(self):
        t = self._make_transaction(status="R")
        assert t.can_transition_to("P") is False
        assert t.can_transition_to("D") is False
        assert t.can_transition_to("F") is False

    def test_transition_status_success(self):
        t = self._make_transaction(status="P")
        result = t.transition_status("D", "USER01")
        assert result is True
        assert t.status == "D"
        assert t.process_user == "USER01"
        assert t.process_date is not None

    def test_transition_status_failure(self):
        t = self._make_transaction(status="P")
        result = t.transition_status("R", "USER01")
        assert result is False
        assert t.status == "P"  # unchanged


class TestTransactionCalculations:
    """Test Transaction.calculate_transaction_amount() and update_amount()"""

    def test_calculate_amount(self):
        t = Transaction(
            date=date(2024, 1, 15),
            time=time(9, 30, 0),
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="BU",
            quantity=Decimal("100.0000"),
            price=Decimal("150.5000"),
            status="P",
        )
        result = t.calculate_transaction_amount()
        assert result == Decimal("15050.0000")

    def test_calculate_amount_no_quantity(self):
        t = Transaction(
            date=date(2024, 1, 15),
            time=time(9, 30, 0),
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="BU",
            quantity=None,
            price=Decimal("150.0000"),
            status="P",
        )
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_calculate_amount_no_price(self):
        t = Transaction(
            date=date(2024, 1, 15),
            time=time(9, 30, 0),
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="BU",
            quantity=Decimal("100.0000"),
            price=None,
            status="P",
        )
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_update_amount(self):
        t = Transaction(
            date=date(2024, 1, 15),
            time=time(9, 30, 0),
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="BU",
            quantity=Decimal("50.0000"),
            price=Decimal("200.0000"),
            status="P",
        )
        t.update_amount()
        assert t.amount == Decimal("10000.0000")


class TestTransactionToDict:
    """Test Transaction.to_dict()"""

    def test_to_dict(self):
        t = Transaction(
            date=date(2024, 1, 15),
            time=time(9, 30, 0),
            portfolio_id="PORT0001",
            sequence_no="000001",
            investment_id="AAPL123456",
            type="BU",
            quantity=Decimal("100.0000"),
            price=Decimal("150.0000"),
            amount=Decimal("15000.00"),
            currency="USD",
            status="P",
            process_date=datetime(2024, 1, 15, 10, 0, 0),
            process_user="USER01",
        )
        d = t.to_dict()
        assert d["date"] == "2024-01-15"
        assert d["time"] == "09:30:00"
        assert d["portfolio_id"] == "PORT0001"
        assert d["sequence_no"] == "000001"
        assert d["investment_id"] == "AAPL123456"
        assert d["type"] == "BU"
        assert d["quantity"] == 100.0
        assert d["price"] == 150.0
        assert d["amount"] == 15000.0
        assert d["currency"] == "USD"
        assert d["status"] == "P"
        assert d["process_user"] == "USER01"

    def test_to_dict_none_values(self):
        t = Transaction(
            date=None,
            time=None,
            portfolio_id="PORT0001",
            sequence_no="000001",
            type="FE",
            status="P",
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
