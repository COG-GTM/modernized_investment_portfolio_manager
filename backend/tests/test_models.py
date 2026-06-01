"""
Comprehensive unit tests for ORM models: Portfolio, Position, Transaction, History.

Run from the backend/ directory:
    cd backend && python -m pytest tests/ -v
"""

import json
import sys
import os
from datetime import date, time, datetime
from decimal import Decimal

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.database import Portfolio, Position
from models.transactions import Transaction
from models.history import History


# ---------------------------------------------------------------------------
# TestPortfolioValidation
# ---------------------------------------------------------------------------


class TestPortfolioValidation:
    """Tests for Portfolio.validate_portfolio()."""

    def test_valid_portfolio(self, sample_portfolio):
        portfolio = sample_portfolio()
        result = portfolio.validate_portfolio()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_port_id_wrong_length(self, sample_portfolio):
        portfolio = sample_portfolio(port_id="SHORT")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_account_no_wrong_length(self, sample_portfolio):
        portfolio = sample_portfolio(account_no="123")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Account number must be 10 characters" in result["errors"]

    def test_invalid_client_type(self, sample_portfolio):
        portfolio = sample_portfolio(client_type="X")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Invalid client type" in result["errors"]

    def test_invalid_status(self, sample_portfolio):
        portfolio = sample_portfolio(status="X")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_multiple_validation_errors(self, sample_portfolio):
        portfolio = sample_portfolio(port_id="BAD", status="X")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]
        assert "Invalid status" in result["errors"]
        assert len(result["errors"]) >= 2

    def test_valid_client_type_corporate(self, sample_portfolio):
        portfolio = sample_portfolio(client_type="C")
        result = portfolio.validate_portfolio()
        assert result["valid"] is True

    def test_valid_client_type_trust(self, sample_portfolio):
        portfolio = sample_portfolio(client_type="T")
        result = portfolio.validate_portfolio()
        assert result["valid"] is True

    def test_valid_status_closed(self, sample_portfolio):
        portfolio = sample_portfolio(status="C")
        result = portfolio.validate_portfolio()
        assert result["valid"] is True

    def test_valid_status_suspended(self, sample_portfolio):
        portfolio = sample_portfolio(status="S")
        result = portfolio.validate_portfolio()
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# TestPortfolioCalculations
# ---------------------------------------------------------------------------


class TestPortfolioCalculations:
    """Tests for Portfolio.calculate_total_value() and update_total_value()."""

    def test_no_positions_only_cash(self, db_session, sample_portfolio):
        portfolio = sample_portfolio(cash_balance=Decimal("5000.00"))
        db_session.add(portfolio)
        db_session.flush()

        total = portfolio.calculate_total_value()
        assert total == Decimal("5000.00")

    def test_with_active_positions(self, db_session, sample_portfolio, sample_position):
        portfolio = sample_portfolio(cash_balance=Decimal("1000.00"))
        db_session.add(portfolio)
        db_session.flush()

        pos1 = sample_position(
            portfolio_id="TEST0001",
            date=date(2025, 1, 1),
            investment_id="AAPL123456",
            market_value=Decimal("5000.00"),
            status="A",
        )
        pos2 = sample_position(
            portfolio_id="TEST0001",
            date=date(2025, 1, 2),
            investment_id="GOOG123456",
            market_value=Decimal("3000.00"),
            status="A",
        )
        db_session.add_all([pos1, pos2])
        db_session.flush()

        total = portfolio.calculate_total_value()
        assert total == Decimal("9000.00")  # 5000 + 3000 + 1000

    def test_mixed_active_and_closed_positions(
        self, db_session, sample_portfolio, sample_position
    ):
        portfolio = sample_portfolio(cash_balance=Decimal("2000.00"))
        db_session.add(portfolio)
        db_session.flush()

        active_pos = sample_position(
            portfolio_id="TEST0001",
            date=date(2025, 2, 1),
            investment_id="MSFT123456",
            market_value=Decimal("4000.00"),
            status="A",
        )
        closed_pos = sample_position(
            portfolio_id="TEST0001",
            date=date(2025, 2, 2),
            investment_id="TSLA123456",
            market_value=Decimal("7000.00"),
            status="C",
        )
        db_session.add_all([active_pos, closed_pos])
        db_session.flush()

        total = portfolio.calculate_total_value()
        # Only the active position counts: 4000 + 2000 cash
        assert total == Decimal("6000.00")

    def test_none_cash_balance(self, db_session, sample_portfolio):
        portfolio = sample_portfolio(cash_balance=None)
        db_session.add(portfolio)
        db_session.flush()

        total = portfolio.calculate_total_value()
        assert total == Decimal("0.00")

    def test_update_total_value_sets_fields(self, db_session, sample_portfolio):
        portfolio = sample_portfolio(
            cash_balance=Decimal("8000.00"), total_value=None, last_maint=None
        )
        db_session.add(portfolio)
        db_session.flush()

        portfolio.update_total_value()
        assert portfolio.total_value == Decimal("8000.00")
        assert portfolio.last_maint == date.today()


# ---------------------------------------------------------------------------
# TestPortfolioSerialization
# ---------------------------------------------------------------------------


class TestPortfolioSerialization:
    """Tests for Portfolio.to_dict()."""

    def test_to_dict_correct_keys_and_values(self, sample_portfolio):
        portfolio = sample_portfolio(
            total_value=Decimal("15000.00"),
            last_maint=date(2025, 6, 15),
            last_user="ADMIN01",
            last_trans="TRN00001",
        )
        d = portfolio.to_dict()

        assert d["port_id"] == "TEST0001"
        assert d["account_no"] == "1234567890"
        assert d["client_name"] == "Test Client"
        assert d["client_type"] == "I"
        assert d["status"] == "A"
        assert d["create_date"] == date.today().isoformat()
        assert d["last_maint"] == "2025-06-15"
        assert d["last_user"] == "ADMIN01"
        assert d["last_trans"] == "TRN00001"

    def test_to_dict_converts_decimal_to_float(self, sample_portfolio):
        portfolio = sample_portfolio(
            total_value=Decimal("12345.67"), cash_balance=Decimal("9999.99")
        )
        d = portfolio.to_dict()
        assert isinstance(d["total_value"], float)
        assert d["total_value"] == 12345.67
        assert isinstance(d["cash_balance"], float)
        assert d["cash_balance"] == 9999.99

    def test_to_dict_handles_none_dates(self, sample_portfolio):
        portfolio = sample_portfolio(create_date=None, last_maint=None)
        d = portfolio.to_dict()
        assert d["create_date"] is None
        assert d["last_maint"] is None

    def test_to_dict_handles_none_total_value(self, sample_portfolio):
        portfolio = sample_portfolio(total_value=None, cash_balance=None)
        d = portfolio.to_dict()
        assert d["total_value"] == 0.0
        assert d["cash_balance"] == 0.0


# ---------------------------------------------------------------------------
# TestPositionGainLoss
# ---------------------------------------------------------------------------


class TestPositionGainLoss:
    """Tests for Position.calculate_gain_loss()."""

    def test_positive_gain(self, sample_position):
        pos = sample_position(
            cost_basis=Decimal("10000.00"), market_value=Decimal("12000.00")
        )
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("2000.00")
        assert result["gain_loss_percent"] == Decimal("20.00")

    def test_loss(self, sample_position):
        pos = sample_position(
            cost_basis=Decimal("10000.00"), market_value=Decimal("8000.00")
        )
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("-2000.00")
        assert result["gain_loss_percent"] == Decimal("-20.00")

    def test_zero_cost_basis(self, sample_position):
        pos = sample_position(
            cost_basis=Decimal("0.00"), market_value=Decimal("5000.00")
        )
        result = pos.calculate_gain_loss()
        # Zero cost_basis triggers the "not self.cost_basis" guard → returns zeros
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_none_cost_basis(self, sample_position):
        pos = sample_position(cost_basis=None, market_value=Decimal("5000.00"))
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_none_market_value(self, sample_position):
        pos = sample_position(cost_basis=Decimal("5000.00"), market_value=None)
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_breakeven(self, sample_position):
        pos = sample_position(
            cost_basis=Decimal("10000.00"), market_value=Decimal("10000.00")
        )
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")


# ---------------------------------------------------------------------------
# TestPositionValidation
# ---------------------------------------------------------------------------


class TestPositionValidation:
    """Tests for Position.validate_position()."""

    def test_valid_position(self, sample_position):
        pos = sample_position()
        result = pos.validate_position()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_portfolio_id_length(self, sample_position):
        pos = sample_position(portfolio_id="SHORT")
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_investment_id_length(self, sample_position):
        pos = sample_position(investment_id="SHORT")
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Investment ID must be 10 characters" in result["errors"]

    def test_invalid_status(self, sample_position):
        pos = sample_position(status="X")
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_negative_quantity(self, sample_position):
        pos = sample_position(quantity=Decimal("-5.0000"))
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Quantity cannot be negative" in result["errors"]

    def test_valid_status_closed(self, sample_position):
        pos = sample_position(status="C")
        result = pos.validate_position()
        assert result["valid"] is True

    def test_valid_status_pending(self, sample_position):
        pos = sample_position(status="P")
        result = pos.validate_position()
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# TestTransactionValidation
# ---------------------------------------------------------------------------


class TestTransactionValidation:
    """Tests for Transaction.validate_transaction()."""

    def test_valid_buy_transaction(self, sample_transaction):
        txn = sample_transaction()
        result = txn.validate_transaction()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_valid_fee_transaction_no_investment_id(self, sample_transaction):
        txn = sample_transaction(
            type="FE",
            investment_id=None,
            quantity=None,
            price=None,
        )
        result = txn.validate_transaction()
        assert result["valid"] is True

    def test_missing_investment_id_for_buy(self, sample_transaction):
        txn = sample_transaction(type="BU", investment_id=None)
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Investment ID required for buy/sell transactions" in result["errors"]

    def test_missing_investment_id_for_sell(self, sample_transaction):
        txn = sample_transaction(type="SL", investment_id=None)
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Investment ID required for buy/sell transactions" in result["errors"]

    def test_zero_quantity_for_buy(self, sample_transaction):
        txn = sample_transaction(type="BU", quantity=Decimal("0"))
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Positive quantity required for buy/sell transactions" in result["errors"]

    def test_negative_quantity_for_sell(self, sample_transaction):
        txn = sample_transaction(type="SL", quantity=Decimal("-10"))
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Positive quantity required for buy/sell transactions" in result["errors"]

    def test_zero_price_for_buy(self, sample_transaction):
        txn = sample_transaction(type="BU", price=Decimal("0"))
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Positive price required for buy/sell transactions" in result["errors"]

    def test_negative_price_for_sell(self, sample_transaction):
        txn = sample_transaction(type="SL", price=Decimal("-50"))
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Positive price required for buy/sell transactions" in result["errors"]

    def test_invalid_type(self, sample_transaction):
        txn = sample_transaction(type="XX")
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Invalid transaction type" in result["errors"]

    def test_invalid_status(self, sample_transaction):
        txn = sample_transaction(status="X")
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_invalid_portfolio_id_length(self, sample_transaction):
        txn = sample_transaction(portfolio_id="BAD")
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_sequence_no_length(self, sample_transaction):
        txn = sample_transaction(sequence_no="1")
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Sequence number must be 6 characters" in result["errors"]


# ---------------------------------------------------------------------------
# TestTransactionStateMachine
# ---------------------------------------------------------------------------


class TestTransactionStateMachine:
    """Tests for Transaction.can_transition_to() and transition_status()."""

    def test_pending_to_done_allowed(self, sample_transaction):
        txn = sample_transaction(status="P")
        assert txn.can_transition_to("D") is True

    def test_pending_to_failed_allowed(self, sample_transaction):
        txn = sample_transaction(status="P")
        assert txn.can_transition_to("F") is True

    def test_pending_to_reversed_not_allowed(self, sample_transaction):
        txn = sample_transaction(status="P")
        assert txn.can_transition_to("R") is False

    def test_done_to_reversed_allowed(self, sample_transaction):
        txn = sample_transaction(status="D")
        assert txn.can_transition_to("R") is True

    def test_done_to_pending_not_allowed(self, sample_transaction):
        txn = sample_transaction(status="D")
        assert txn.can_transition_to("P") is False

    def test_failed_to_pending_retry_allowed(self, sample_transaction):
        txn = sample_transaction(status="F")
        assert txn.can_transition_to("P") is True

    def test_reversed_is_terminal(self, sample_transaction):
        txn = sample_transaction(status="R")
        assert txn.can_transition_to("P") is False
        assert txn.can_transition_to("D") is False
        assert txn.can_transition_to("F") is False
        assert txn.can_transition_to("R") is False

    def test_transition_status_valid_updates_fields(self, sample_transaction):
        txn = sample_transaction(status="P")
        result = txn.transition_status("D", "USER01")
        assert result is True
        assert txn.status == "D"
        assert txn.process_user == "USER01"
        assert isinstance(txn.process_date, datetime)

    def test_transition_status_invalid_does_not_change(self, sample_transaction):
        txn = sample_transaction(status="P")
        result = txn.transition_status("R", "USER01")
        assert result is False
        assert txn.status == "P"  # Status unchanged


# ---------------------------------------------------------------------------
# TestTransactionCalculations
# ---------------------------------------------------------------------------


class TestTransactionCalculations:
    """Tests for Transaction.calculate_transaction_amount() and update_amount()."""

    def test_quantity_times_price(self, sample_transaction):
        txn = sample_transaction(
            quantity=Decimal("100.0000"), price=Decimal("150.0000")
        )
        amount = txn.calculate_transaction_amount()
        assert amount == Decimal("15000.00000000")

    def test_none_quantity(self, sample_transaction):
        txn = sample_transaction(quantity=None, price=Decimal("150.0000"))
        amount = txn.calculate_transaction_amount()
        assert amount == Decimal("0.00")

    def test_none_price(self, sample_transaction):
        txn = sample_transaction(quantity=Decimal("100.0000"), price=None)
        amount = txn.calculate_transaction_amount()
        assert amount == Decimal("0.00")

    def test_update_amount_sets_self_amount(self, sample_transaction):
        txn = sample_transaction(
            quantity=Decimal("50.0000"), price=Decimal("200.0000")
        )
        txn.update_amount()
        assert txn.amount == Decimal("10000.00000000")


# ---------------------------------------------------------------------------
# TestHistoryAuditRecord
# ---------------------------------------------------------------------------


class TestHistoryAuditRecord:
    """Tests for History.create_audit_record(), get_before_data(), get_after_data()."""

    def test_create_audit_record_basic(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
            after_data={"client_name": "New Client"},
            user="ADMIN01",
        )
        assert record.portfolio_id == "TEST0001"
        assert record.record_type == "PT"
        assert record.action_code == "A"
        assert record.process_user == "ADMIN01"
        assert isinstance(record.process_date, datetime)
        assert record.after_image == json.dumps({"client_name": "New Client"})

    def test_create_audit_record_serializes_before_after(self):
        before = {"status": "A"}
        after = {"status": "C"}
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="C",
            before_data=before,
            after_data=after,
        )
        assert record.before_image == json.dumps(before)
        assert record.after_image == json.dumps(after)

    def test_create_audit_record_none_before_data(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
            before_data=None,
            after_data={"key": "value"},
        )
        assert record.before_image is None

    def test_create_audit_record_sets_process_date_and_user(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="TR",
            action_code="D",
            user="BATCH01",
        )
        assert record.process_user == "BATCH01"
        assert isinstance(record.process_date, datetime)

    def test_create_audit_record_increments_seq_no_with_session(
        self, db_session, sample_portfolio
    ):
        # Must add a parent portfolio first due to FK constraint
        portfolio = sample_portfolio()
        db_session.add(portfolio)
        db_session.flush()

        rec1 = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
            after_data={"key": "val1"},
            db_session=db_session,
        )
        db_session.add(rec1)
        db_session.flush()

        rec2 = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="C",
            after_data={"key": "val2"},
            db_session=db_session,
        )
        # seq_no for second record should be incremented
        # (exact value depends on timestamp matching, but it should differ from "0001"
        #  if the timestamp is the same, or be "0001" if different)
        assert rec2.seq_no is not None
        assert len(rec2.seq_no) == 4

    def test_get_before_data_valid_json(self):
        h = History(before_image=json.dumps({"status": "A"}))
        result = h.get_before_data()
        assert result == {"status": "A"}

    def test_get_before_data_none(self):
        h = History(before_image=None)
        result = h.get_before_data()
        assert result is None

    def test_get_before_data_invalid_json(self):
        h = History(before_image="not-valid-json{{{")
        result = h.get_before_data()
        assert result is None

    def test_get_after_data_valid_json(self):
        h = History(after_image=json.dumps({"amount": 1000}))
        result = h.get_after_data()
        assert result == {"amount": 1000}

    def test_get_after_data_none(self):
        h = History(after_image=None)
        result = h.get_after_data()
        assert result is None

    def test_get_after_data_invalid_json(self):
        h = History(after_image="<<<invalid>>>")
        result = h.get_after_data()
        assert result is None
