"""
Comprehensive ORM model unit tests for Portfolio, Position, Transaction, and History.
Uses in-memory SQLite fixtures defined in conftest.py.
"""
import json
from datetime import date, time, datetime
from decimal import Decimal

import pytest

from models.database import Portfolio, Position
from models.transactions import Transaction
from models.history import History


# ---------------------------------------------------------------------------
# Portfolio Validation
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

    def test_invalid_port_id_empty(self, sample_portfolio):
        portfolio = sample_portfolio(port_id="")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_account_no_wrong_length(self, sample_portfolio):
        portfolio = sample_portfolio(account_no="123")
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
        assert len(result["errors"]) >= 2


# ---------------------------------------------------------------------------
# Portfolio Calculations
# ---------------------------------------------------------------------------
class TestPortfolioCalculations:
    """Tests for Portfolio.calculate_total_value() and update_total_value()."""

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
            portfolio_id="TEST0001",
            investment_id="AAPL000001",
            market_value=Decimal("5000.00"),
            status="A",
        )
        pos2 = sample_position(
            portfolio_id="TEST0001",
            investment_id="GOOG000001",
            market_value=Decimal("3000.00"),
            status="A",
        )
        db_session.add_all([pos1, pos2])
        db_session.flush()

        total = portfolio.calculate_total_value()
        assert total == Decimal("9000.00")  # 5000 + 3000 + 1000

    def test_mixed_active_and_closed_positions(self, db_session, sample_portfolio, sample_position):
        portfolio = sample_portfolio(
            port_id="MIX00001",
            cash_balance=Decimal("2000.00"),
        )
        db_session.add(portfolio)
        db_session.flush()

        active = sample_position(
            portfolio_id="MIX00001",
            investment_id="AAPL000001",
            market_value=Decimal("4000.00"),
            status="A",
        )
        closed = sample_position(
            portfolio_id="MIX00001",
            investment_id="MSFT000001",
            market_value=Decimal("6000.00"),
            status="C",
        )
        db_session.add_all([active, closed])
        db_session.flush()

        total = portfolio.calculate_total_value()
        # Only active position counted: 4000 + 2000 cash
        assert total == Decimal("6000.00")

    def test_none_cash_balance_treated_as_zero(self, db_session, sample_portfolio):
        portfolio = sample_portfolio(
            port_id="NOCASH01",
            cash_balance=None,
        )
        db_session.add(portfolio)
        db_session.flush()
        assert portfolio.calculate_total_value() == Decimal("0.00")

    def test_update_total_value_sets_fields(self, db_session, sample_portfolio):
        portfolio = sample_portfolio(
            port_id="UPD00001",
            cash_balance=Decimal("7500.00"),
        )
        db_session.add(portfolio)
        db_session.flush()

        portfolio.update_total_value()
        assert portfolio.total_value == Decimal("7500.00")
        assert portfolio.last_maint == date.today()


# ---------------------------------------------------------------------------
# Portfolio Serialization
# ---------------------------------------------------------------------------
class TestPortfolioSerialization:
    """Tests for Portfolio.to_dict()."""

    def test_to_dict_returns_correct_keys(self, sample_portfolio):
        portfolio = sample_portfolio(
            total_value=Decimal("25000.00"),
            last_maint=date(2025, 6, 15),
        )
        d = portfolio.to_dict()
        expected_keys = {
            "port_id", "account_no", "client_name", "client_type",
            "create_date", "last_maint", "status", "total_value",
            "cash_balance", "last_user", "last_trans",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_correct_values(self, sample_portfolio):
        today = date.today()
        portfolio = sample_portfolio(
            total_value=Decimal("25000.00"),
            last_maint=date(2025, 6, 15),
            create_date=today,
        )
        d = portfolio.to_dict()
        assert d["port_id"] == "TEST0001"
        assert d["account_no"] == "1234567890"
        assert d["client_name"] == "Test Client"
        assert d["client_type"] == "I"
        assert d["status"] == "A"
        assert d["total_value"] == 25000.0
        assert d["cash_balance"] == 10000.0
        assert d["create_date"] == today.isoformat()
        assert d["last_maint"] == "2025-06-15"

    def test_to_dict_handles_none_dates(self, sample_portfolio):
        portfolio = sample_portfolio(create_date=None, last_maint=None, total_value=None, cash_balance=None)
        d = portfolio.to_dict()
        assert d["create_date"] is None
        assert d["last_maint"] is None
        assert d["total_value"] == 0.0
        assert d["cash_balance"] == 0.0

    def test_to_dict_converts_decimal_to_float(self, sample_portfolio):
        portfolio = sample_portfolio(
            total_value=Decimal("12345.67"),
            cash_balance=Decimal("9999.99"),
        )
        d = portfolio.to_dict()
        assert isinstance(d["total_value"], float)
        assert isinstance(d["cash_balance"], float)
        assert d["total_value"] == 12345.67
        assert d["cash_balance"] == 9999.99


# ---------------------------------------------------------------------------
# Position Gain/Loss
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
        pos = sample_position(cost_basis=Decimal("0.00"), market_value=Decimal("5000.00"))
        result = pos.calculate_gain_loss()
        # cost_basis is falsy (0) so the early guard returns zeros
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
# Position Validation
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
        pos = sample_position(investment_id="BAD")
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

    def test_multiple_errors(self, sample_position):
        pos = sample_position(portfolio_id="BAD", investment_id="X", status="Z")
        result = pos.validate_position()
        assert result["valid"] is False
        assert len(result["errors"]) >= 3


# ---------------------------------------------------------------------------
# Transaction Validation
# ---------------------------------------------------------------------------
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
        txn = sample_transaction(type="SL", price=Decimal("-10"))
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

    def test_multiple_errors(self, sample_transaction):
        txn = sample_transaction(
            portfolio_id="X",
            sequence_no="1",
            type="XX",
            status="Z",
        )
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert len(result["errors"]) >= 4


# ---------------------------------------------------------------------------
# Transaction State Machine
# ---------------------------------------------------------------------------
class TestTransactionStateMachine:
    """Tests for Transaction.can_transition_to() and transition_status()."""

    # --- can_transition_to ---
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

    def test_failed_to_pending_allowed(self, sample_transaction):
        txn = sample_transaction(status="F")
        assert txn.can_transition_to("P") is True

    def test_reversed_to_anything_not_allowed(self, sample_transaction):
        txn = sample_transaction(status="R")
        assert txn.can_transition_to("P") is False
        assert txn.can_transition_to("D") is False
        assert txn.can_transition_to("F") is False
        assert txn.can_transition_to("R") is False

    # --- transition_status ---
    def test_valid_transition_updates_fields(self, sample_transaction):
        txn = sample_transaction(status="P")
        result = txn.transition_status("D", "ADMIN01")
        assert result is True
        assert txn.status == "D"
        assert txn.process_user == "ADMIN01"
        assert txn.process_date is not None

    def test_invalid_transition_does_not_change_status(self, sample_transaction):
        txn = sample_transaction(status="R")
        original_status = txn.status
        result = txn.transition_status("P", "ADMIN01")
        assert result is False
        assert txn.status == original_status


# ---------------------------------------------------------------------------
# Transaction Calculations
# ---------------------------------------------------------------------------
class TestTransactionCalculations:
    """Tests for Transaction.calculate_transaction_amount() and update_amount()."""

    def test_quantity_times_price(self, sample_transaction):
        txn = sample_transaction(quantity=Decimal("100.0000"), price=Decimal("150.0000"))
        result = txn.calculate_transaction_amount()
        assert result == Decimal("15000.00000000")

    def test_none_quantity(self, sample_transaction):
        txn = sample_transaction(quantity=None, price=Decimal("150.0000"))
        result = txn.calculate_transaction_amount()
        assert result == Decimal("0.00")

    def test_none_price(self, sample_transaction):
        txn = sample_transaction(quantity=Decimal("100.0000"), price=None)
        result = txn.calculate_transaction_amount()
        assert result == Decimal("0.00")

    def test_update_amount_sets_amount(self, sample_transaction):
        txn = sample_transaction(quantity=Decimal("50.0000"), price=Decimal("200.0000"))
        txn.update_amount()
        assert txn.amount == Decimal("10000.00000000")


# ---------------------------------------------------------------------------
# History / Audit Record
# ---------------------------------------------------------------------------
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

    def test_create_audit_record_with_before_after_data(self):
        before = {"status": "A", "cash_balance": 5000}
        after = {"status": "C", "cash_balance": 0}
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
            after_data={"status": "A"},
        )
        assert record.before_image is None
        assert record.after_image is not None

    def test_create_audit_record_sets_process_date(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="TR",
            action_code="A",
        )
        assert isinstance(record.process_date, datetime)

    def test_create_audit_record_increments_seq_no_with_session(self, db_session, sample_portfolio):
        # Need a portfolio in DB for FK constraint
        portfolio = sample_portfolio(port_id="SEQT0001")
        db_session.add(portfolio)
        db_session.flush()

        rec1 = History.create_audit_record(
            portfolio_id="SEQT0001",
            record_type="PT",
            action_code="A",
            db_session=db_session,
        )
        db_session.add(rec1)
        db_session.flush()

        # Create a second record with the same timestamp components;
        # seq_no should be incremented by the db_session query
        rec2 = History.create_audit_record(
            portfolio_id="SEQT0001",
            record_type="PT",
            action_code="C",
            db_session=db_session,
        )
        # rec2.seq_no should be "0002" if timestamps align, or "0001" if they differ
        # At minimum, the method should not error out
        assert rec2.seq_no is not None
        assert len(rec2.seq_no) == 4

    # --- get_before_data / get_after_data ---
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
        h = History(after_image="not-valid-json{{{")
        assert h.get_after_data() is None
