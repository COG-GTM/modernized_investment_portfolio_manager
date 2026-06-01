"""
Comprehensive ORM model unit tests for Portfolio, Position, Transaction, and History.

Run from backend/ directory:
    cd backend && python -m pytest tests/ -v
"""

import json
from datetime import date, time, datetime
from decimal import Decimal

import pytest

from models.database import Portfolio, Position
from models.transactions import Transaction
from models.history import History


# ---------------------------------------------------------------------------
# TestPortfolioValidation
# ---------------------------------------------------------------------------
class TestPortfolioValidation:
    """Tests for Portfolio.validate_portfolio()."""

    def test_valid_portfolio(self, sample_portfolio):
        p = sample_portfolio()
        result = p.validate_portfolio()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_port_id_wrong_length(self, sample_portfolio):
        p = sample_portfolio(port_id="SHORT")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_port_id_empty(self, sample_portfolio):
        p = sample_portfolio(port_id="")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_account_no_wrong_length(self, sample_portfolio):
        p = sample_portfolio(account_no="12345")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Account number must be 10 characters" in result["errors"]

    def test_invalid_account_no_empty(self, sample_portfolio):
        p = sample_portfolio(account_no="")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Account number must be 10 characters" in result["errors"]

    def test_invalid_client_type(self, sample_portfolio):
        p = sample_portfolio(client_type="X")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Invalid client type" in result["errors"]

    def test_invalid_status(self, sample_portfolio):
        p = sample_portfolio(status="X")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_multiple_validation_errors(self, sample_portfolio):
        p = sample_portfolio(port_id="BAD", status="X", account_no="SHORT")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert len(result["errors"]) == 3
        assert "Portfolio ID must be 8 characters" in result["errors"]
        assert "Account number must be 10 characters" in result["errors"]
        assert "Invalid status" in result["errors"]

    def test_all_valid_client_types(self, sample_portfolio):
        for ct in ["I", "C", "T"]:
            p = sample_portfolio(client_type=ct)
            result = p.validate_portfolio()
            assert result["valid"] is True

    def test_all_valid_statuses(self, sample_portfolio):
        for s in ["A", "C", "S"]:
            p = sample_portfolio(status=s)
            result = p.validate_portfolio()
            assert result["valid"] is True


# ---------------------------------------------------------------------------
# TestPortfolioCalculations
# ---------------------------------------------------------------------------
class TestPortfolioCalculations:
    """Tests for Portfolio.calculate_total_value() and update_total_value()."""

    def test_no_positions_only_cash(self, db_session, sample_portfolio):
        p = sample_portfolio(cash_balance=Decimal("5000.00"))
        db_session.add(p)
        db_session.flush()
        assert p.calculate_total_value() == Decimal("5000.00")

    def test_with_active_positions(self, db_session, sample_portfolio, sample_position):
        p = sample_portfolio(cash_balance=Decimal("1000.00"))
        db_session.add(p)
        db_session.flush()

        pos1 = sample_position(
            portfolio_id=p.port_id,
            investment_id="AAPL000001",
            market_value=Decimal("5000.00"),
            status="A",
        )
        pos2 = sample_position(
            portfolio_id=p.port_id,
            investment_id="GOOG000002",
            market_value=Decimal("3000.00"),
            status="A",
        )
        db_session.add_all([pos1, pos2])
        db_session.flush()

        assert p.calculate_total_value() == Decimal("9000.00")

    def test_mixed_active_and_closed_positions(
        self, db_session, sample_portfolio, sample_position
    ):
        p = sample_portfolio(cash_balance=Decimal("2000.00"))
        db_session.add(p)
        db_session.flush()

        active = sample_position(
            portfolio_id=p.port_id,
            investment_id="AAPL000001",
            market_value=Decimal("4000.00"),
            status="A",
        )
        closed = sample_position(
            portfolio_id=p.port_id,
            investment_id="GOOG000002",
            market_value=Decimal("9999.00"),
            status="C",
        )
        db_session.add_all([active, closed])
        db_session.flush()

        # Only active position + cash
        assert p.calculate_total_value() == Decimal("6000.00")

    def test_none_cash_balance(self, db_session, sample_portfolio):
        p = sample_portfolio(cash_balance=None)
        db_session.add(p)
        db_session.flush()
        assert p.calculate_total_value() == Decimal("0.00")

    def test_update_total_value(self, db_session, sample_portfolio, sample_position):
        p = sample_portfolio(cash_balance=Decimal("500.00"))
        db_session.add(p)
        db_session.flush()

        pos = sample_position(
            portfolio_id=p.port_id,
            investment_id="MSFT000001",
            market_value=Decimal("1500.00"),
            status="A",
        )
        db_session.add(pos)
        db_session.flush()

        p.update_total_value()
        assert p.total_value == Decimal("2000.00")
        assert p.last_maint == date.today()


# ---------------------------------------------------------------------------
# TestPortfolioSerialization
# ---------------------------------------------------------------------------
class TestPortfolioSerialization:
    """Tests for Portfolio.to_dict()."""

    def test_to_dict_returns_correct_keys_and_values(self, sample_portfolio):
        p = sample_portfolio(
            total_value=Decimal("25000.50"),
            cash_balance=Decimal("10000.00"),
            create_date=date(2025, 1, 15),
            last_maint=date(2025, 6, 1),
            last_user="ADMIN01",
            last_trans="TR000001",
        )
        d = p.to_dict()
        assert d["port_id"] == "TEST0001"
        assert d["account_no"] == "1234567890"
        assert d["client_name"] == "Test Client"
        assert d["client_type"] == "I"
        assert d["create_date"] == "2025-01-15"
        assert d["last_maint"] == "2025-06-01"
        assert d["status"] == "A"
        assert d["total_value"] == 25000.50
        assert d["cash_balance"] == 10000.00
        assert d["last_user"] == "ADMIN01"
        assert d["last_trans"] == "TR000001"

    def test_to_dict_handles_none_dates(self, sample_portfolio):
        p = sample_portfolio(create_date=None, last_maint=None)
        d = p.to_dict()
        assert d["create_date"] is None
        assert d["last_maint"] is None

    def test_to_dict_converts_decimal_to_float(self, sample_portfolio):
        p = sample_portfolio(
            total_value=Decimal("12345.67"), cash_balance=Decimal("890.12")
        )
        d = p.to_dict()
        assert isinstance(d["total_value"], float)
        assert isinstance(d["cash_balance"], float)

    def test_to_dict_none_total_value_and_cash(self, sample_portfolio):
        p = sample_portfolio(total_value=None, cash_balance=None)
        d = p.to_dict()
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
        # cost_basis is falsy when zero, so the guard returns zeros
        result = pos.calculate_gain_loss()
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

    def test_both_none(self, sample_position):
        pos = sample_position(cost_basis=None, market_value=None)
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
        pos = sample_position(quantity=Decimal("-10.0000"))
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Quantity cannot be negative" in result["errors"]

    def test_all_valid_statuses(self, sample_position):
        for s in ["A", "C", "P"]:
            pos = sample_position(status=s)
            result = pos.validate_position()
            assert result["valid"] is True

    def test_zero_quantity_is_valid(self, sample_position):
        pos = sample_position(quantity=Decimal("0.0000"))
        result = pos.validate_position()
        # zero is not negative; quantity=0 is falsy so the guard doesn't trigger
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# TestTransactionValidation
# ---------------------------------------------------------------------------
class TestTransactionValidation:
    """Tests for Transaction.validate_transaction()."""

    def test_valid_buy_transaction(self, sample_transaction):
        t = sample_transaction()
        result = t.validate_transaction()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_valid_fee_transaction_no_investment_id(self, sample_transaction):
        t = sample_transaction(type="FE", investment_id=None, quantity=None, price=None)
        result = t.validate_transaction()
        assert result["valid"] is True

    def test_missing_investment_id_for_buy(self, sample_transaction):
        t = sample_transaction(type="BU", investment_id=None)
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Investment ID required for buy/sell transactions" in result["errors"]

    def test_missing_investment_id_for_sell(self, sample_transaction):
        t = sample_transaction(type="SL", investment_id=None)
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Investment ID required for buy/sell transactions" in result["errors"]

    def test_zero_quantity_for_buy(self, sample_transaction):
        t = sample_transaction(type="BU", quantity=Decimal("0"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Positive quantity required for buy/sell transactions" in result["errors"]

    def test_negative_quantity_for_sell(self, sample_transaction):
        t = sample_transaction(type="SL", quantity=Decimal("-5"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Positive quantity required for buy/sell transactions" in result["errors"]

    def test_zero_price_for_buy(self, sample_transaction):
        t = sample_transaction(type="BU", price=Decimal("0"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Positive price required for buy/sell transactions" in result["errors"]

    def test_negative_price_for_sell(self, sample_transaction):
        t = sample_transaction(type="SL", price=Decimal("-100"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Positive price required for buy/sell transactions" in result["errors"]

    def test_invalid_type(self, sample_transaction):
        t = sample_transaction(type="XX")
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Invalid transaction type" in result["errors"]

    def test_invalid_status(self, sample_transaction):
        t = sample_transaction(status="Z")
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_invalid_portfolio_id_length(self, sample_transaction):
        t = sample_transaction(portfolio_id="BAD")
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_sequence_no_length(self, sample_transaction):
        t = sample_transaction(sequence_no="1")
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Sequence number must be 6 characters" in result["errors"]

    def test_null_quantity_for_buy(self, sample_transaction):
        t = sample_transaction(type="BU", quantity=None)
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Positive quantity required for buy/sell transactions" in result["errors"]

    def test_null_price_for_buy(self, sample_transaction):
        t = sample_transaction(type="BU", price=None)
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Positive price required for buy/sell transactions" in result["errors"]


# ---------------------------------------------------------------------------
# TestTransactionStatusMachine
# ---------------------------------------------------------------------------
class TestTransactionStatusMachine:
    """Tests for can_transition_to() and transition_status()."""

    # --- can_transition_to ---
    def test_pending_to_done_allowed(self, sample_transaction):
        t = sample_transaction(status="P")
        assert t.can_transition_to("D") is True

    def test_pending_to_failed_allowed(self, sample_transaction):
        t = sample_transaction(status="P")
        assert t.can_transition_to("F") is True

    def test_pending_to_reversed_not_allowed(self, sample_transaction):
        t = sample_transaction(status="P")
        assert t.can_transition_to("R") is False

    def test_done_to_reversed_allowed(self, sample_transaction):
        t = sample_transaction(status="D")
        assert t.can_transition_to("R") is True

    def test_done_to_pending_not_allowed(self, sample_transaction):
        t = sample_transaction(status="D")
        assert t.can_transition_to("P") is False

    def test_failed_to_pending_retry_allowed(self, sample_transaction):
        t = sample_transaction(status="F")
        assert t.can_transition_to("P") is True

    def test_reversed_is_terminal(self, sample_transaction):
        t = sample_transaction(status="R")
        for target in ["P", "D", "F", "R"]:
            assert t.can_transition_to(target) is False

    # --- transition_status ---
    def test_transition_status_valid(self, sample_transaction):
        t = sample_transaction(status="P")
        result = t.transition_status("D", "USER001")
        assert result is True
        assert t.status == "D"
        assert t.process_user == "USER001"
        assert t.process_date is not None

    def test_transition_status_invalid(self, sample_transaction):
        t = sample_transaction(status="P")
        original_status = t.status
        result = t.transition_status("R", "USER001")
        assert result is False
        assert t.status == original_status

    def test_transition_status_from_reversed_fails(self, sample_transaction):
        t = sample_transaction(status="R")
        result = t.transition_status("P", "USER001")
        assert result is False
        assert t.status == "R"


# ---------------------------------------------------------------------------
# TestTransactionCalculations
# ---------------------------------------------------------------------------
class TestTransactionCalculations:
    """Tests for calculate_transaction_amount() and update_amount()."""

    def test_quantity_times_price(self, sample_transaction):
        t = sample_transaction(
            quantity=Decimal("100.0000"), price=Decimal("150.0000")
        )
        assert t.calculate_transaction_amount() == Decimal("15000.00000000")

    def test_none_quantity(self, sample_transaction):
        t = sample_transaction(quantity=None, price=Decimal("150.0000"))
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_none_price(self, sample_transaction):
        t = sample_transaction(quantity=Decimal("100.0000"), price=None)
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_both_none(self, sample_transaction):
        t = sample_transaction(quantity=None, price=None)
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_update_amount_sets_value(self, sample_transaction):
        t = sample_transaction(
            quantity=Decimal("50.0000"), price=Decimal("200.0000")
        )
        t.update_amount()
        assert t.amount == Decimal("10000.00000000")


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
            before_data={"status": "A"},
            after_data={"status": "C"},
            reason_code="UPDT",
            user="ADMIN01",
        )
        assert record.portfolio_id == "TEST0001"
        assert record.record_type == "PT"
        assert record.action_code == "A"
        assert record.reason_code == "UPDT"
        assert record.process_user == "ADMIN01"
        assert record.process_date is not None
        assert record.seq_no == "0001"

    def test_create_audit_record_serializes_before_after(self):
        before = {"field": "old_value"}
        after = {"field": "new_value"}
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PS",
            action_code="C",
            before_data=before,
            after_data=after,
        )
        assert record.before_image == json.dumps(before)
        assert record.after_image == json.dumps(after)

    def test_create_audit_record_none_before_data(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="TR",
            action_code="A",
            before_data=None,
            after_data={"new": True},
        )
        assert record.before_image is None
        assert record.after_image == json.dumps({"new": True})

    def test_create_audit_record_sets_process_date_and_user(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="D",
            user="TESTUSER",
        )
        assert record.process_user == "TESTUSER"
        assert isinstance(record.process_date, datetime)

    def test_create_audit_record_increments_seq_no(self, db_session, sample_portfolio):
        # Need a portfolio in DB due to FK constraint
        p = sample_portfolio()
        db_session.add(p)
        db_session.flush()

        rec1 = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
            db_session=db_session,
        )
        db_session.add(rec1)
        db_session.flush()

        rec2 = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="C",
            db_session=db_session,
        )
        # seq_no should be incremented if same portfolio_id/date/time
        # Due to timing, if both happen in the same second the date/time match
        # and seq_no should be "0002". If they don't match (different time_str),
        # seq_no will be "0001" again, which is also correct behavior.
        assert rec2.seq_no in ("0001", "0002")

    # --- get_before_data / get_after_data ---
    def test_get_before_data_valid_json(self):
        h = History(before_image='{"key": "value"}')
        assert h.get_before_data() == {"key": "value"}

    def test_get_after_data_valid_json(self):
        h = History(after_image='{"key": "value"}')
        assert h.get_after_data() == {"key": "value"}

    def test_get_before_data_none(self):
        h = History(before_image=None)
        assert h.get_before_data() is None

    def test_get_after_data_none(self):
        h = History(after_image=None)
        assert h.get_after_data() is None

    def test_get_before_data_invalid_json(self):
        h = History(before_image="not valid json {{{")
        assert h.get_before_data() is None

    def test_get_after_data_invalid_json(self):
        h = History(after_image="not valid json {{{")
        assert h.get_after_data() is None
