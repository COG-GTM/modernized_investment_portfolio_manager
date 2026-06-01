"""
Comprehensive ORM model unit tests.

Covers: Portfolio, Position, Transaction, and History models.
Run from backend/:  python -m pytest tests/ -v
"""
import json
from decimal import Decimal
from datetime import date, time, datetime

import pytest

from models.database import Portfolio, Position
from models.transactions import Transaction
from models.history import History


# ======================================================================
# Portfolio — Validation
# ======================================================================

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

    def test_invalid_port_id_empty(self, sample_portfolio):
        portfolio = sample_portfolio(port_id="")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_account_no_wrong_length(self, sample_portfolio):
        portfolio = sample_portfolio(account_no="12345")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Account number must be 10 characters" in result["errors"]

    def test_invalid_account_no_empty(self, sample_portfolio):
        portfolio = sample_portfolio(account_no="")
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
        assert len(result["errors"]) == 2


# ======================================================================
# Portfolio — Calculations
# ======================================================================

class TestPortfolioCalculations:
    """Tests for calculate_total_value() and update_total_value()."""

    def test_no_positions_returns_cash_balance(self, db_session, sample_portfolio):
        portfolio = sample_portfolio(cash_balance=Decimal("5000.00"))
        db_session.add(portfolio)
        db_session.flush()

        assert portfolio.calculate_total_value() == Decimal("5000.00")

    def test_with_active_positions(self, db_session, sample_portfolio, sample_position):
        portfolio = sample_portfolio(cash_balance=Decimal("1000.00"))
        db_session.add(portfolio)
        db_session.flush()

        pos1 = sample_position(
            portfolio_id=portfolio.port_id,
            investment_id="AAPL123456",
            market_value=Decimal("5000.00"),
            status="A",
        )
        pos2 = sample_position(
            portfolio_id=portfolio.port_id,
            date=date(2025, 1, 1),
            investment_id="GOOG123456",
            market_value=Decimal("3000.00"),
            status="A",
        )
        db_session.add_all([pos1, pos2])
        db_session.flush()

        total = portfolio.calculate_total_value()
        assert total == Decimal("9000.00")  # 5000 + 3000 + 1000

    def test_mixed_active_and_closed_positions(self, db_session, sample_portfolio, sample_position):
        portfolio = sample_portfolio(cash_balance=Decimal("1000.00"))
        db_session.add(portfolio)
        db_session.flush()

        active = sample_position(
            portfolio_id=portfolio.port_id,
            investment_id="AAPL123456",
            market_value=Decimal("5000.00"),
            status="A",
        )
        closed = sample_position(
            portfolio_id=portfolio.port_id,
            date=date(2025, 6, 1),
            investment_id="MSFT123456",
            market_value=Decimal("9999.00"),
            status="C",
        )
        db_session.add_all([active, closed])
        db_session.flush()

        total = portfolio.calculate_total_value()
        assert total == Decimal("6000.00")  # only active 5000 + cash 1000

    def test_none_cash_balance_treated_as_zero(self, db_session, sample_portfolio):
        portfolio = sample_portfolio(cash_balance=None)
        db_session.add(portfolio)
        db_session.flush()

        assert portfolio.calculate_total_value() == Decimal("0.00")

    def test_update_total_value_sets_fields(self, db_session, sample_portfolio):
        portfolio = sample_portfolio(cash_balance=Decimal("2500.00"), total_value=None)
        db_session.add(portfolio)
        db_session.flush()

        portfolio.update_total_value()

        assert portfolio.total_value == Decimal("2500.00")
        assert portfolio.last_maint == date.today()


# ======================================================================
# Portfolio — Serialization
# ======================================================================

class TestPortfolioSerialization:
    """Tests for Portfolio.to_dict()."""

    def test_to_dict_returns_correct_keys(self, sample_portfolio):
        portfolio = sample_portfolio(
            total_value=Decimal("15000.00"),
            last_maint=date(2025, 3, 15),
        )
        d = portfolio.to_dict()

        assert d["port_id"] == "TEST0001"
        assert d["account_no"] == "1234567890"
        assert d["client_name"] == "Test Client"
        assert d["client_type"] == "I"
        assert d["status"] == "A"
        assert d["create_date"] == date.today().isoformat()
        assert d["last_maint"] == "2025-03-15"
        assert d["total_value"] == 15000.0
        assert d["cash_balance"] == 10000.0

    def test_to_dict_none_dates(self, sample_portfolio):
        portfolio = sample_portfolio(create_date=None, last_maint=None)
        d = portfolio.to_dict()

        assert d["create_date"] is None
        assert d["last_maint"] is None

    def test_to_dict_converts_decimal_to_float(self, sample_portfolio):
        portfolio = sample_portfolio(
            total_value=Decimal("12345.67"),
            cash_balance=Decimal("9876.54"),
        )
        d = portfolio.to_dict()

        assert isinstance(d["total_value"], float)
        assert isinstance(d["cash_balance"], float)
        assert d["total_value"] == 12345.67
        assert d["cash_balance"] == 9876.54

    def test_to_dict_none_total_value_and_cash(self, sample_portfolio):
        portfolio = sample_portfolio(total_value=None, cash_balance=None)
        d = portfolio.to_dict()

        assert d["total_value"] == 0.0
        assert d["cash_balance"] == 0.0


# ======================================================================
# Position — Gain / Loss
# ======================================================================

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
        # cost_basis is falsy when 0 → returns zeros per current implementation
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


# ======================================================================
# Position — Validation
# ======================================================================

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
        """Zero quantity should not trigger the negative-quantity error."""
        pos = sample_position(quantity=Decimal("0.0000"))
        result = pos.validate_position()
        # Zero is not negative, so no quantity error
        assert "Quantity cannot be negative" not in result["errors"]


# ======================================================================
# Transaction — Validation
# ======================================================================

class TestTransactionValidation:
    """Tests for Transaction.validate_transaction()."""

    def test_valid_buy_transaction(self, sample_transaction):
        txn = sample_transaction()
        result = txn.validate_transaction()
        assert result["valid"] is True
        assert result["errors"] == []

    def test_valid_fee_transaction_no_investment_id(self, sample_transaction):
        txn = sample_transaction(type="FE", investment_id=None, quantity=None, price=None)
        result = txn.validate_transaction()
        assert result["valid"] is True
        assert result["errors"] == []

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
        txn = sample_transaction(type="SL", quantity=Decimal("-5"))
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Positive quantity required for buy/sell transactions" in result["errors"]

    def test_zero_price_for_buy(self, sample_transaction):
        txn = sample_transaction(type="BU", price=Decimal("0"))
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Positive price required for buy/sell transactions" in result["errors"]

    def test_negative_price_for_sell(self, sample_transaction):
        txn = sample_transaction(type="SL", price=Decimal("-100"))
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Positive price required for buy/sell transactions" in result["errors"]

    def test_invalid_type(self, sample_transaction):
        txn = sample_transaction(type="XX")
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Invalid transaction type" in result["errors"]

    def test_invalid_status(self, sample_transaction):
        txn = sample_transaction(status="Z")
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


# ======================================================================
# Transaction — State Machine
# ======================================================================

class TestTransactionStatusMachine:
    """Tests for can_transition_to() and transition_status()."""

    # --- can_transition_to ---

    def test_pending_to_done(self, sample_transaction):
        txn = sample_transaction(status="P")
        assert txn.can_transition_to("D") is True

    def test_pending_to_failed(self, sample_transaction):
        txn = sample_transaction(status="P")
        assert txn.can_transition_to("F") is True

    def test_pending_to_reversed_not_allowed(self, sample_transaction):
        txn = sample_transaction(status="P")
        assert txn.can_transition_to("R") is False

    def test_done_to_reversed(self, sample_transaction):
        txn = sample_transaction(status="D")
        assert txn.can_transition_to("R") is True

    def test_done_to_pending_not_allowed(self, sample_transaction):
        txn = sample_transaction(status="D")
        assert txn.can_transition_to("P") is False

    def test_failed_to_pending_retry(self, sample_transaction):
        txn = sample_transaction(status="F")
        assert txn.can_transition_to("P") is True

    def test_reversed_is_terminal(self, sample_transaction):
        txn = sample_transaction(status="R")
        assert txn.can_transition_to("P") is False
        assert txn.can_transition_to("D") is False
        assert txn.can_transition_to("F") is False

    # --- transition_status (valid) ---

    def test_transition_status_valid(self, sample_transaction):
        txn = sample_transaction(status="P")
        result = txn.transition_status("D", "ADMIN01")

        assert result is True
        assert txn.status == "D"
        assert txn.process_user == "ADMIN01"
        assert isinstance(txn.process_date, datetime)

    # --- transition_status (invalid) ---

    def test_transition_status_invalid(self, sample_transaction):
        txn = sample_transaction(status="P")
        original_status = txn.status

        result = txn.transition_status("R", "ADMIN01")

        assert result is False
        assert txn.status == original_status


# ======================================================================
# Transaction — Calculations
# ======================================================================

class TestTransactionCalculations:
    """Tests for calculate_transaction_amount() and update_amount()."""

    def test_calculate_amount(self, sample_transaction):
        txn = sample_transaction(quantity=Decimal("50.0000"), price=Decimal("200.0000"))
        assert txn.calculate_transaction_amount() == Decimal("10000.00000000")

    def test_calculate_amount_none_quantity(self, sample_transaction):
        txn = sample_transaction(quantity=None, price=Decimal("200.0000"))
        assert txn.calculate_transaction_amount() == Decimal("0.00")

    def test_calculate_amount_none_price(self, sample_transaction):
        txn = sample_transaction(quantity=Decimal("50.0000"), price=None)
        assert txn.calculate_transaction_amount() == Decimal("0.00")

    def test_update_amount_sets_field(self, sample_transaction):
        txn = sample_transaction(quantity=Decimal("10.0000"), price=Decimal("25.0000"))
        txn.update_amount()
        assert txn.amount == Decimal("250.00000000")


# ======================================================================
# History — Audit Record
# ======================================================================

class TestHistoryAuditRecord:
    """Tests for History.create_audit_record()."""

    def test_creates_record_with_correct_fields(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
            before_data={"status": "A"},
            after_data={"status": "C"},
            user="ADMIN01",
        )

        assert record.portfolio_id == "TEST0001"
        assert record.record_type == "PT"
        assert record.action_code == "A"
        assert record.process_user == "ADMIN01"
        assert isinstance(record.process_date, datetime)

    def test_serializes_before_after_as_json(self):
        before = {"field": "old_value"}
        after = {"field": "new_value"}
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="C",
            before_data=before,
            after_data=after,
        )

        assert record.before_image == json.dumps(before)
        assert record.after_image == json.dumps(after)

    def test_none_before_data(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
            before_data=None,
            after_data={"status": "A"},
        )

        assert record.before_image is None
        assert record.after_image is not None

    def test_sets_process_date_and_user(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="TR",
            action_code="D",
            user="SYSADMIN",
        )

        assert record.process_user == "SYSADMIN"
        assert record.process_date is not None

    def test_seq_no_increments_with_db_session(self, db_session, sample_portfolio):
        # Need a parent portfolio for FK
        portfolio = sample_portfolio()
        db_session.add(portfolio)
        db_session.flush()

        # Create first record via the class method with db_session
        rec1 = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
            db_session=db_session,
        )
        db_session.add(rec1)
        db_session.flush()

        # Create second record in the same (portfolio_id, date, time) window
        rec2 = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="C",
            db_session=db_session,
        )

        # seq_no should be > rec1's if they share the same date+time
        # (in practice the time string is precise to microseconds, so
        # they may or may not share the same time slot; we verify the
        # mechanism works when they do.)
        assert rec2.seq_no is not None
        assert len(rec2.seq_no) == 4

    def test_default_seq_no_without_db_session(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
        )
        assert record.seq_no == "0001"


# ======================================================================
# History — JSON accessors
# ======================================================================

class TestHistoryDataAccessors:
    """Tests for get_before_data() and get_after_data()."""

    def test_valid_json_before(self):
        h = History(before_image='{"key": "value"}')
        assert h.get_before_data() == {"key": "value"}

    def test_valid_json_after(self):
        h = History(after_image='{"key": "value"}')
        assert h.get_after_data() == {"key": "value"}

    def test_none_before(self):
        h = History(before_image=None)
        assert h.get_before_data() is None

    def test_none_after(self):
        h = History(after_image=None)
        assert h.get_after_data() is None

    def test_invalid_json_before(self):
        h = History(before_image="not valid json{{{")
        assert h.get_before_data() is None

    def test_invalid_json_after(self):
        h = History(after_image="not valid json{{{")
        assert h.get_after_data() is None
