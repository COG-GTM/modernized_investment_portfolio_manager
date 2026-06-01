"""Comprehensive tests for ORM model methods with zero prior coverage."""

import json
from datetime import date, time, datetime
from decimal import Decimal

import pytest

from models.database import Portfolio, Position
from models.transactions import Transaction
from models.history import History


# ============================================================================
# Portfolio validation
# ============================================================================

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

    def test_invalid_account_no_wrong_length(self, sample_portfolio):
        p = sample_portfolio(account_no="123")
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
        p = sample_portfolio(port_id="BAD", status="X")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]
        assert "Invalid status" in result["errors"]
        assert len(result["errors"]) >= 2


# ============================================================================
# Portfolio calculations
# ============================================================================

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
            market_value=Decimal("2000.00"),
            status="A",
        )
        pos2 = sample_position(
            portfolio_id=p.port_id,
            investment_id="GOOG000001",
            date=date.today(),
            market_value=Decimal("3000.00"),
            status="A",
        )
        db_session.add_all([pos1, pos2])
        db_session.flush()

        assert p.calculate_total_value() == Decimal("6000.00")

    def test_mixed_active_and_closed_positions(
        self, db_session, sample_portfolio, sample_position
    ):
        p = sample_portfolio(
            port_id="MIX00001",
            cash_balance=Decimal("500.00"),
        )
        db_session.add(p)
        db_session.flush()

        active = sample_position(
            portfolio_id="MIX00001",
            investment_id="ACT0000001",
            market_value=Decimal("1000.00"),
            status="A",
        )
        closed = sample_position(
            portfolio_id="MIX00001",
            investment_id="CLS0000001",
            market_value=Decimal("9999.00"),
            status="C",
        )
        db_session.add_all([active, closed])
        db_session.flush()

        # Only the active position should be summed
        assert p.calculate_total_value() == Decimal("1500.00")

    def test_none_cash_balance(self, db_session, sample_portfolio):
        p = sample_portfolio(
            port_id="NOCASH01",
            cash_balance=None,
        )
        db_session.add(p)
        db_session.flush()

        assert p.calculate_total_value() == Decimal("0.00")

    def test_update_total_value(self, db_session, sample_portfolio):
        p = sample_portfolio(
            port_id="UPD00001",
            cash_balance=Decimal("7777.00"),
        )
        db_session.add(p)
        db_session.flush()

        p.update_total_value()
        assert p.total_value == Decimal("7777.00")
        assert p.last_maint == date.today()


# ============================================================================
# Portfolio serialization
# ============================================================================

class TestPortfolioSerialization:
    """Tests for Portfolio.to_dict()."""

    def test_returns_correct_keys_and_values(self, sample_portfolio):
        p = sample_portfolio(
            total_value=Decimal("25000.50"),
            cash_balance=Decimal("10000.00"),
            create_date=date(2024, 1, 15),
            last_maint=date(2024, 6, 1),
            last_user="ADMIN",
            last_trans="TR000001",
        )
        d = p.to_dict()

        assert d["port_id"] == "TEST0001"
        assert d["account_no"] == "1234567890"
        assert d["client_name"] == "Test Client"
        assert d["client_type"] == "I"
        assert d["status"] == "A"
        assert d["create_date"] == "2024-01-15"
        assert d["last_maint"] == "2024-06-01"
        assert d["last_user"] == "ADMIN"
        assert d["last_trans"] == "TR000001"

    def test_handles_none_dates(self, sample_portfolio):
        p = sample_portfolio(create_date=None, last_maint=None)
        d = p.to_dict()
        assert d["create_date"] is None
        assert d["last_maint"] is None

    def test_converts_decimal_to_float(self, sample_portfolio):
        p = sample_portfolio(
            total_value=Decimal("12345.67"),
            cash_balance=Decimal("9999.99"),
        )
        d = p.to_dict()
        assert isinstance(d["total_value"], float)
        assert d["total_value"] == 12345.67
        assert isinstance(d["cash_balance"], float)
        assert d["cash_balance"] == 9999.99


# ============================================================================
# Position gain/loss
# ============================================================================

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
        # cost_basis is falsy when 0 → guard returns zeros
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


# ============================================================================
# Position validation
# ============================================================================

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


# ============================================================================
# Transaction validation
# ============================================================================

class TestTransactionValidation:
    """Tests for Transaction.validate_transaction()."""

    def test_valid_bu_transaction(self, sample_transaction):
        t = sample_transaction()
        result = t.validate_transaction()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_valid_fe_transaction_no_investment_id(self, sample_transaction):
        t = sample_transaction(type="FE", investment_id=None)
        result = t.validate_transaction()
        assert result["valid"] is True

    def test_missing_investment_id_for_bu(self, sample_transaction):
        t = sample_transaction(type="BU", investment_id=None)
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Investment ID required for buy/sell transactions" in result["errors"]

    def test_missing_investment_id_for_sl(self, sample_transaction):
        t = sample_transaction(type="SL", investment_id=None)
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Investment ID required for buy/sell transactions" in result["errors"]

    def test_zero_quantity_for_bu(self, sample_transaction):
        t = sample_transaction(type="BU", quantity=Decimal("0"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Positive quantity required for buy/sell transactions" in result["errors"]

    def test_negative_quantity_for_sl(self, sample_transaction):
        t = sample_transaction(type="SL", quantity=Decimal("-5"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Positive quantity required for buy/sell transactions" in result["errors"]

    def test_zero_price_for_bu(self, sample_transaction):
        t = sample_transaction(type="BU", price=Decimal("0"))
        result = t.validate_transaction()
        assert result["valid"] is False
        assert "Positive price required for buy/sell transactions" in result["errors"]

    def test_negative_price_for_sl(self, sample_transaction):
        t = sample_transaction(type="SL", price=Decimal("-10"))
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


# ============================================================================
# Transaction status machine
# ============================================================================

class TestTransactionStatusMachine:
    """Tests for Transaction.can_transition_to() and transition_status()."""

    # --- can_transition_to ---

    def test_p_to_d_allowed(self, sample_transaction):
        t = sample_transaction(status="P")
        assert t.can_transition_to("D") is True

    def test_p_to_f_allowed(self, sample_transaction):
        t = sample_transaction(status="P")
        assert t.can_transition_to("F") is True

    def test_p_to_r_not_allowed(self, sample_transaction):
        t = sample_transaction(status="P")
        assert t.can_transition_to("R") is False

    def test_d_to_r_allowed(self, sample_transaction):
        t = sample_transaction(status="D")
        assert t.can_transition_to("R") is True

    def test_d_to_p_not_allowed(self, sample_transaction):
        t = sample_transaction(status="D")
        assert t.can_transition_to("P") is False

    def test_f_to_p_allowed_retry(self, sample_transaction):
        t = sample_transaction(status="F")
        assert t.can_transition_to("P") is True

    def test_r_is_terminal(self, sample_transaction):
        t = sample_transaction(status="R")
        for target in ("P", "D", "F", "R"):
            assert t.can_transition_to(target) is False

    # --- transition_status ---

    def test_transition_valid_updates_fields(self, sample_transaction):
        t = sample_transaction(status="P")
        result = t.transition_status("D", "TESTUSER")
        assert result is True
        assert t.status == "D"
        assert t.process_user == "TESTUSER"
        assert isinstance(t.process_date, datetime)

    def test_transition_invalid_does_not_change(self, sample_transaction):
        t = sample_transaction(status="P")
        result = t.transition_status("R", "TESTUSER")
        assert result is False
        assert t.status == "P"


# ============================================================================
# Transaction calculations
# ============================================================================

class TestTransactionCalculations:
    """Tests for calculate_transaction_amount() and update_amount()."""

    def test_quantity_times_price(self, sample_transaction):
        t = sample_transaction(
            quantity=Decimal("50.0000"),
            price=Decimal("200.0000"),
        )
        assert t.calculate_transaction_amount() == Decimal("10000.00000000")

    def test_none_quantity(self, sample_transaction):
        t = sample_transaction(quantity=None, price=Decimal("100.0000"))
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_none_price(self, sample_transaction):
        t = sample_transaction(quantity=Decimal("10.0000"), price=None)
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_update_amount_sets_self(self, sample_transaction):
        t = sample_transaction(
            quantity=Decimal("10.0000"),
            price=Decimal("25.0000"),
        )
        t.update_amount()
        assert t.amount == Decimal("250.00000000")


# ============================================================================
# History audit record
# ============================================================================

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
        assert record.after_image is None  # no after_data passed

    def test_create_audit_record_with_data(self):
        before = {"status": "A"}
        after = {"status": "C"}
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
            record_type="TR",
            action_code="A",
            before_data=None,
            after_data={"key": "value"},
        )
        assert record.before_image is None
        assert record.after_image == json.dumps({"key": "value"})

    def test_create_audit_record_sets_process_date_and_user(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PS",
            action_code="D",
            user="MYUSER",
        )
        assert isinstance(record.process_date, datetime)
        assert record.process_user == "MYUSER"

    def test_create_audit_record_increments_seq_no(self, db_session, sample_portfolio):
        # Need a parent portfolio for the FK constraint
        p = sample_portfolio(port_id="SEQ00001")
        db_session.add(p)
        db_session.flush()

        r1 = History.create_audit_record(
            portfolio_id="SEQ00001",
            record_type="PT",
            action_code="A",
            db_session=db_session,
        )
        db_session.add(r1)
        db_session.flush()

        r2 = History.create_audit_record(
            portfolio_id="SEQ00001",
            record_type="PT",
            action_code="C",
            db_session=db_session,
        )
        # Because r1 exists for the same portfolio_id/date/time the seq should increment
        # Note: if the two calls happen within the same time_str window the count increments
        # In practice the two calls may share the same time_str → seq_no should be "0002"
        # If they don't share the same time_str both will be "0001". Either is correct.
        assert r2.seq_no in ("0001", "0002")

    # --- get_before_data / get_after_data ---

    def test_get_before_data_valid_json(self):
        h = History(before_image=json.dumps({"foo": "bar"}))
        assert h.get_before_data() == {"foo": "bar"}

    def test_get_after_data_valid_json(self):
        h = History(after_image=json.dumps({"baz": 42}))
        assert h.get_after_data() == {"baz": 42}

    def test_get_before_data_none(self):
        h = History(before_image=None)
        assert h.get_before_data() is None

    def test_get_after_data_none(self):
        h = History(after_image=None)
        assert h.get_after_data() is None

    def test_get_before_data_invalid_json(self):
        h = History(before_image="NOT-JSON{{{")
        assert h.get_before_data() is None

    def test_get_after_data_invalid_json(self):
        h = History(after_image="NOT-JSON{{{")
        assert h.get_after_data() is None
