"""
Comprehensive ORM model unit tests.

Covers: Portfolio, Position, Transaction, and History models.
Run from backend/:  python -m pytest tests/ -v
"""
import json
from decimal import Decimal
from datetime import date, time, datetime
from unittest.mock import patch

import pytest

from models.database import Portfolio, Position
from models.transactions import Transaction
from models.history import History


# ---------------------------------------------------------------------------
# Portfolio validation
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
        p = sample_portfolio(account_no="123")
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
        p = sample_portfolio(port_id="BAD", status="X")
        result = p.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]
        assert "Invalid status" in result["errors"]
        assert len(result["errors"]) == 2


# ---------------------------------------------------------------------------
# Portfolio calculations
# ---------------------------------------------------------------------------
class TestPortfolioCalculations:
    """Tests for Portfolio.calculate_total_value() and update_total_value()."""

    def test_no_positions_cash_only(self, db_session, sample_portfolio):
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
            date=date(2025, 1, 1),
        )
        db_session.add_all([pos1, pos2])
        db_session.flush()

        total = p.calculate_total_value()
        assert total == Decimal("9000.00")  # 5000 + 3000 + 1000

    def test_mixed_active_closed_positions(self, db_session, sample_portfolio, sample_position):
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
            market_value=Decimal("6000.00"),
            status="C",
            date=date(2025, 1, 1),
        )
        db_session.add_all([active, closed])
        db_session.flush()

        total = p.calculate_total_value()
        assert total == Decimal("6000.00")  # 4000 active + 2000 cash; closed excluded

    def test_none_cash_balance(self, db_session, sample_portfolio):
        p = sample_portfolio(cash_balance=None)
        db_session.add(p)
        db_session.flush()
        assert p.calculate_total_value() == Decimal("0.00")

    def test_update_total_value(self, db_session, sample_portfolio):
        p = sample_portfolio(cash_balance=Decimal("7500.00"))
        db_session.add(p)
        db_session.flush()

        p.update_total_value()
        assert p.total_value == Decimal("7500.00")
        assert p.last_maint == date.today()


# ---------------------------------------------------------------------------
# Portfolio serialization
# ---------------------------------------------------------------------------
class TestPortfolioSerialization:
    """Tests for Portfolio.to_dict()."""

    def test_to_dict_correct_keys_and_values(self, sample_portfolio):
        p = sample_portfolio(
            total_value=Decimal("50000.00"),
            cash_balance=Decimal("10000.00"),
            create_date=date(2024, 1, 15),
            last_maint=date(2024, 6, 20),
            last_user="ADMIN",
            last_trans="TR000001",
        )
        d = p.to_dict()
        assert d["port_id"] == "TEST0001"
        assert d["account_no"] == "1234567890"
        assert d["client_name"] == "Test Client"
        assert d["client_type"] == "I"
        assert d["create_date"] == "2024-01-15"
        assert d["last_maint"] == "2024-06-20"
        assert d["status"] == "A"
        assert d["total_value"] == 50000.0
        assert d["cash_balance"] == 10000.0
        assert d["last_user"] == "ADMIN"
        assert d["last_trans"] == "TR000001"

    def test_to_dict_none_dates(self, sample_portfolio):
        p = sample_portfolio(create_date=None, last_maint=None, total_value=None, cash_balance=None)
        d = p.to_dict()
        assert d["create_date"] is None
        assert d["last_maint"] is None
        assert d["total_value"] == 0.0
        assert d["cash_balance"] == 0.0

    def test_to_dict_decimal_to_float_conversion(self, sample_portfolio):
        p = sample_portfolio(
            total_value=Decimal("123456.78"),
            cash_balance=Decimal("9999.99"),
        )
        d = p.to_dict()
        assert isinstance(d["total_value"], float)
        assert isinstance(d["cash_balance"], float)
        assert d["total_value"] == 123456.78
        assert d["cash_balance"] == 9999.99


# ---------------------------------------------------------------------------
# Position gain/loss
# ---------------------------------------------------------------------------
class TestPositionGainLoss:
    """Tests for Position.calculate_gain_loss()."""

    def test_positive_gain(self, sample_position):
        pos = sample_position(cost_basis=Decimal("10000.00"), market_value=Decimal("12000.00"))
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("2000.00")
        assert result["gain_loss_percent"] == Decimal("20.00")

    def test_loss(self, sample_position):
        pos = sample_position(cost_basis=Decimal("10000.00"), market_value=Decimal("8000.00"))
        result = pos.calculate_gain_loss()
        assert result["gain_loss"] == Decimal("-2000.00")
        assert result["gain_loss_percent"] == Decimal("-20.00")

    def test_zero_cost_basis(self, sample_position):
        pos = sample_position(cost_basis=Decimal("0"), market_value=Decimal("5000.00"))
        result = pos.calculate_gain_loss()
        # Zero cost_basis is falsy → returns zeros (current behavior)
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


# ---------------------------------------------------------------------------
# Position validation
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
        pos = sample_position(quantity=Decimal("-10"))
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Quantity cannot be negative" in result["errors"]

    def test_zero_quantity_is_valid(self, sample_position):
        pos = sample_position(quantity=Decimal("0"))
        result = pos.validate_position()
        # Zero quantity is not < 0, so no error
        assert "Quantity cannot be negative" not in result["errors"]


# ---------------------------------------------------------------------------
# Transaction validation
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
        assert result["errors"] == []

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


# ---------------------------------------------------------------------------
# Transaction state machine
# ---------------------------------------------------------------------------
class TestTransactionStateMachine:
    """Tests for Transaction.can_transition_to() and transition_status()."""

    def test_pending_to_done(self, sample_transaction):
        t = sample_transaction(status="P")
        assert t.can_transition_to("D") is True

    def test_pending_to_failed(self, sample_transaction):
        t = sample_transaction(status="P")
        assert t.can_transition_to("F") is True

    def test_pending_to_reversed_not_allowed(self, sample_transaction):
        t = sample_transaction(status="P")
        assert t.can_transition_to("R") is False

    def test_done_to_reversed(self, sample_transaction):
        t = sample_transaction(status="D")
        assert t.can_transition_to("R") is True

    def test_done_to_pending_not_allowed(self, sample_transaction):
        t = sample_transaction(status="D")
        assert t.can_transition_to("P") is False

    def test_failed_to_pending_retry(self, sample_transaction):
        t = sample_transaction(status="F")
        assert t.can_transition_to("P") is True

    def test_reversed_is_terminal(self, sample_transaction):
        t = sample_transaction(status="R")
        assert t.can_transition_to("P") is False
        assert t.can_transition_to("D") is False
        assert t.can_transition_to("F") is False
        assert t.can_transition_to("R") is False

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
        assert t.status == original_status  # unchanged


# ---------------------------------------------------------------------------
# Transaction calculations
# ---------------------------------------------------------------------------
class TestTransactionCalculations:
    """Tests for Transaction.calculate_transaction_amount() and update_amount()."""

    def test_calculate_amount(self, sample_transaction):
        t = sample_transaction(quantity=Decimal("100"), price=Decimal("50.25"))
        assert t.calculate_transaction_amount() == Decimal("5025.00")

    def test_calculate_amount_none_quantity(self, sample_transaction):
        t = sample_transaction(quantity=None, price=Decimal("50.00"))
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_calculate_amount_none_price(self, sample_transaction):
        t = sample_transaction(quantity=Decimal("100"), price=None)
        assert t.calculate_transaction_amount() == Decimal("0.00")

    def test_update_amount(self, sample_transaction):
        t = sample_transaction(quantity=Decimal("200"), price=Decimal("10.00"))
        t.update_amount()
        assert t.amount == Decimal("2000.00")


# ---------------------------------------------------------------------------
# History audit record
# ---------------------------------------------------------------------------
class TestHistoryAuditRecord:
    """Tests for History.create_audit_record(), get_before_data(), get_after_data()."""

    def test_create_audit_record_basic(self):
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
        assert record.portfolio_id == "TEST0001"
        assert record.record_type == "PT"
        assert record.action_code == "C"
        assert record.before_image == json.dumps(before)
        assert record.after_image == json.dumps(after)
        assert record.process_user == "ADMIN01"
        assert record.process_date is not None
        assert record.reason_code == "AUTO"

    def test_create_audit_record_none_before(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
            before_data=None,
            after_data={"client_name": "New"},
        )
        assert record.before_image is None
        assert record.after_image is not None

    def test_create_audit_record_with_db_session_increments_seq(self, db_session, sample_portfolio):
        # Need a portfolio in the DB for the FK
        p = sample_portfolio()
        db_session.add(p)
        db_session.flush()

        # Freeze time so both records get the same date_str and time_str
        frozen = datetime(2026, 3, 26, 12, 0, 0, 123456)
        with patch("models.history.datetime") as mock_dt:
            mock_dt.now.return_value = frozen
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            r1 = History.create_audit_record(
                portfolio_id="TEST0001",
                record_type="PT",
                action_code="A",
                after_data={"a": 1},
                db_session=db_session,
            )
            db_session.add(r1)
            db_session.flush()

            r2 = History.create_audit_record(
                portfolio_id="TEST0001",
                record_type="PT",
                action_code="C",
                after_data={"a": 2},
                db_session=db_session,
            )
        # r1 seq_no=0001 (no existing), r2 seq_no=0002 (one existing)
        assert r1.seq_no == "0001"
        assert r2.seq_no == "0002"

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
        h = History(before_image="not-json{{{")
        assert h.get_before_data() is None

    def test_get_after_data_invalid_json(self):
        h = History(after_image="not-json{{{")
        assert h.get_after_data() is None

    def test_create_audit_record_sets_process_date(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="TR",
            action_code="D",
        )
        assert isinstance(record.process_date, datetime)
        assert record.process_user == "SYSTEM"  # default
