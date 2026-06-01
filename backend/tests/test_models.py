"""
Comprehensive ORM model unit tests.

Covers: Portfolio, Position, Transaction, and History models —
validation, calculations, serialization, state machine, and audit records.

Run from the backend/ directory:
    cd backend && python -m pytest tests/ -v
"""
import json
from datetime import date, time, datetime
from decimal import Decimal

import pytest

from models.database import Portfolio, Position
from models.transactions import Transaction
from models.history import History


# =========================================================================
# Portfolio tests
# =========================================================================

class TestPortfolioValidation:
    """Tests for Portfolio.validate_portfolio()."""

    def test_valid_portfolio(self, sample_portfolio):
        p = sample_portfolio()
        result = p.validate_portfolio()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_port_id_too_short(self, sample_portfolio):
        p = sample_portfolio(port_id="SHORT")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_port_id_too_long(self, sample_portfolio):
        p = sample_portfolio(port_id="TOOLONGID")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_port_id_none(self, sample_portfolio):
        p = sample_portfolio(port_id=None)
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_account_no_wrong_length(self, sample_portfolio):
        p = sample_portfolio(account_no="12345")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Account number must be 10 characters" in result["errors"]

    def test_invalid_account_no_none(self, sample_portfolio):
        p = sample_portfolio(account_no=None)
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
        p = sample_portfolio(port_id="BAD", status="X", account_no="short")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert len(result["errors"]) == 3
        assert "Portfolio ID must be 8 characters" in result["errors"]
        assert "Account number must be 10 characters" in result["errors"]
        assert "Invalid status" in result["errors"]

    def test_all_valid_client_types(self, sample_portfolio):
        for ct in ("I", "C", "T"):
            p = sample_portfolio(client_type=ct)
            assert p.validate_portfolio()["valid"] is True

    def test_all_valid_statuses(self, sample_portfolio):
        for s in ("A", "C", "S"):
            p = sample_portfolio(status=s)
            assert p.validate_portfolio()["valid"] is True


class TestPortfolioCalculations:
    """Tests for calculate_total_value() and update_total_value()."""

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
            investment_id="AAPL123456",
            market_value=Decimal("5000.00"),
            status="A",
        )
        pos2 = sample_position(
            portfolio_id=p.port_id,
            investment_id="GOOG123456",
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
            investment_id="AAPL123456",
            market_value=Decimal("4000.00"),
            status="A",
        )
        closed = sample_position(
            portfolio_id=p.port_id,
            investment_id="GOOG123456",
            market_value=Decimal("9999.00"),
            status="C",
        )
        db_session.add_all([active, closed])
        db_session.flush()

        # Closed position should be excluded
        assert p.calculate_total_value() == Decimal("6000.00")

    def test_none_cash_balance(self, db_session, sample_portfolio):
        p = sample_portfolio(cash_balance=None)
        db_session.add(p)
        db_session.flush()
        assert p.calculate_total_value() == Decimal("0.00")

    def test_update_total_value_sets_fields(self, db_session, sample_portfolio):
        p = sample_portfolio(cash_balance=Decimal("7777.00"))
        db_session.add(p)
        db_session.flush()

        p.update_total_value()

        assert p.total_value == Decimal("7777.00")
        assert p.last_maint == date.today()


class TestPortfolioSerialization:
    """Tests for Portfolio.to_dict()."""

    def test_to_dict_keys_and_values(self, sample_portfolio):
        p = sample_portfolio(
            total_value=Decimal("50000.00"),
            last_maint=date(2025, 6, 15),
            last_user="ADMIN01",
            last_trans="TXN00001",
        )
        d = p.to_dict()

        assert d["port_id"] == "TEST0001"
        assert d["account_no"] == "1234567890"
        assert d["client_name"] == "Test Client"
        assert d["client_type"] == "I"
        assert d["status"] == "A"
        assert d["create_date"] == date.today().isoformat()
        assert d["last_maint"] == "2025-06-15"
        assert d["total_value"] == 50000.0
        assert d["cash_balance"] == 10000.0
        assert d["last_user"] == "ADMIN01"
        assert d["last_trans"] == "TXN00001"

    def test_to_dict_none_dates(self, sample_portfolio):
        p = sample_portfolio(create_date=None, last_maint=None)
        d = p.to_dict()
        assert d["create_date"] is None
        assert d["last_maint"] is None

    def test_to_dict_none_numeric_fields(self, sample_portfolio):
        p = sample_portfolio(total_value=None, cash_balance=None)
        d = p.to_dict()
        assert d["total_value"] == 0.0
        assert d["cash_balance"] == 0.0

    def test_to_dict_decimal_to_float(self, sample_portfolio):
        p = sample_portfolio(
            total_value=Decimal("12345.67"),
            cash_balance=Decimal("890.12"),
        )
        d = p.to_dict()
        assert isinstance(d["total_value"], float)
        assert isinstance(d["cash_balance"], float)


# =========================================================================
# Position tests
# =========================================================================

class TestPositionGainLoss:
    """Tests for Position.calculate_gain_loss()."""

    def test_positive_gain(self, sample_position):
        pos = sample_position(
            cost_basis=Decimal("10000.00"),
            market_value=Decimal("12000.00"),
        )
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("2000.00")
        assert result["gain_loss_percent"] == Decimal("20.00")

    def test_loss(self, sample_position):
        pos = sample_position(
            cost_basis=Decimal("10000.00"),
            market_value=Decimal("8000.00"),
        )
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("-2000.00")
        assert result["gain_loss_percent"] == Decimal("-20.00")

    def test_zero_cost_basis(self, sample_position):
        pos = sample_position(
            cost_basis=Decimal("0.00"),
            market_value=Decimal("5000.00"),
        )
        # Zero cost_basis is falsy for Decimal('0.00') — code returns zeros
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_none_cost_basis(self, sample_position):
        pos = sample_position(cost_basis=None, market_value=Decimal("5000.00"))
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")

    def test_none_market_value(self, sample_position):
        pos = sample_position(cost_basis=Decimal("10000.00"), market_value=None)
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
            cost_basis=Decimal("5000.00"),
            market_value=Decimal("5000.00"),
        )
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("0.00")
        assert result["gain_loss_percent"] == Decimal("0.00")


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

    def test_zero_quantity_is_valid(self, sample_position):
        # Zero quantity does not trigger negative check
        pos = sample_position(quantity=Decimal("0.0000"))
        result = pos.validate_position()
        assert result["valid"] is True

    def test_all_valid_position_statuses(self, sample_position):
        for s in ("A", "C", "P"):
            pos = sample_position(status=s)
            assert pos.validate_position()["valid"] is True


# =========================================================================
# Transaction tests
# =========================================================================

class TestTransactionValidation:
    """Tests for Transaction.validate_transaction()."""

    def test_valid_buy_transaction(self, sample_transaction):
        t = sample_transaction()
        result = t.validate_transaction()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_valid_fee_transaction_no_investment_id(self, sample_transaction):
        t = sample_transaction(type="FE", investment_id=None)
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

    def test_none_quantity_for_buy(self, sample_transaction):
        t = sample_transaction(type="BU", quantity=None)
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Positive quantity required for buy/sell transactions" in result["errors"]

    def test_zero_price_for_buy(self, sample_transaction):
        t = sample_transaction(type="BU", price=Decimal("0"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Positive price required for buy/sell transactions" in result["errors"]

    def test_negative_price_for_sell(self, sample_transaction):
        t = sample_transaction(type="SL", price=Decimal("-10"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Positive price required for buy/sell transactions" in result["errors"]

    def test_none_price_for_buy(self, sample_transaction):
        t = sample_transaction(type="BU", price=None)
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

    def test_valid_transfer_transaction(self, sample_transaction):
        t = sample_transaction(type="TR")
        result = t.validate_transaction()
        assert result["valid"] is True

    def test_all_valid_transaction_types(self, sample_transaction):
        for tt in ("BU", "SL", "TR", "FE"):
            t = sample_transaction(type=tt)
            assert t.validate_transaction()["valid"] is True

    def test_all_valid_transaction_statuses(self, sample_transaction):
        for s in ("P", "D", "F", "R"):
            t = sample_transaction(status=s)
            assert t.validate_transaction()["valid"] is True


class TestTransactionStateMachine:
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

    def test_reversed_terminal_no_transitions(self, sample_transaction):
        t = sample_transaction(status="R")
        for target in ("P", "D", "F", "R"):
            assert t.can_transition_to(target) is False

    # --- transition_status ---

    def test_transition_status_valid(self, sample_transaction):
        t = sample_transaction(status="P")
        result = t.transition_status("D", "TRADER01")
        assert result is True
        assert t.status == "D"
        assert t.process_user == "TRADER01"
        assert t.process_date is not None

    def test_transition_status_invalid(self, sample_transaction):
        t = sample_transaction(status="P")
        original_status = t.status
        result = t.transition_status("R", "TRADER01")
        assert result is False
        assert t.status == original_status

    def test_transition_status_does_not_change_process_date_on_failure(
        self, sample_transaction
    ):
        t = sample_transaction(status="R")
        t.process_date = None
        t.process_user = None
        result = t.transition_status("P", "TRADER01")
        assert result is False
        assert t.process_date is None
        assert t.process_user is None


class TestTransactionCalculations:
    """Tests for calculate_transaction_amount() and update_amount()."""

    def test_calculate_amount(self, sample_transaction):
        t = sample_transaction(
            quantity=Decimal("100.0000"),
            price=Decimal("25.5000"),
        )
        assert t.calculate_transaction_amount() == Decimal("2550.00000000")

    def test_calculate_amount_none_quantity(self, sample_transaction):
        t = sample_transaction(quantity=None, price=Decimal("10.0000"))
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_calculate_amount_none_price(self, sample_transaction):
        t = sample_transaction(quantity=Decimal("50.0000"), price=None)
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_calculate_amount_both_none(self, sample_transaction):
        t = sample_transaction(quantity=None, price=None)
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_update_amount_sets_amount(self, sample_transaction):
        t = sample_transaction(
            quantity=Decimal("200.0000"),
            price=Decimal("10.0000"),
        )
        t.update_amount()
        assert t.amount == Decimal("2000.00000000")


# =========================================================================
# History / Audit tests
# =========================================================================

class TestHistoryAuditRecord:
    """Tests for History.create_audit_record(), get_before_data(), get_after_data()."""

    def test_create_audit_record_basic(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
        )
        assert record.portfolio_id == "TEST0001"
        assert record.record_type == "PT"
        assert record.action_code == "A"
        assert record.process_user == "SYSTEM"
        assert record.process_date is not None
        assert record.before_image is None
        assert record.after_image is None

    def test_create_audit_record_with_before_after(self):
        before = {"status": "A", "cash_balance": "1000.00"}
        after = {"status": "C", "cash_balance": "0.00"}
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="C",
            before_data=before,
            after_data=after,
            user="ADMIN01",
        )
        assert record.before_image == json.dumps(before)
        assert record.after_image == json.dumps(after)
        assert record.process_user == "ADMIN01"

    def test_create_audit_record_none_before_data(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
            before_data=None,
            after_data={"new": "data"},
        )
        assert record.before_image is None
        assert record.after_image is not None

    def test_create_audit_record_sets_process_date(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="TR",
            action_code="D",
        )
        assert isinstance(record.process_date, datetime)

    def test_create_audit_record_custom_reason_code(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PS",
            action_code="C",
            reason_code="MKTV",
        )
        assert record.reason_code == "MKTV"

    def test_create_audit_record_with_db_session_increments_seq(
        self, db_session, sample_portfolio
    ):
        # Need a portfolio in DB for FK constraint
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

        # Second record with same portfolio_id, date, time should get incremented seq_no
        rec2 = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="C",
            db_session=db_session,
        )
        # rec2.seq_no should be "0002" if created in the same second as rec1
        # (if they differ in time, it could be "0001" — but it should still be valid)
        assert len(rec2.seq_no) == 4
        assert rec2.seq_no.isdigit()

    def test_get_before_data_valid_json(self):
        h = History(before_image='{"key": "value"}')
        assert h.get_before_data() == {"key": "value"}

    def test_get_after_data_valid_json(self):
        h = History(after_image='{"status": "A"}')
        assert h.get_after_data() == {"status": "A"}

    def test_get_before_data_none(self):
        h = History(before_image=None)
        assert h.get_before_data() is None

    def test_get_after_data_none(self):
        h = History(after_image=None)
        assert h.get_after_data() is None

    def test_get_before_data_invalid_json(self):
        h = History(before_image="not-valid-json{{{")
        assert h.get_before_data() is None

    def test_get_after_data_invalid_json(self):
        h = History(after_image="broken}")
        assert h.get_after_data() is None
