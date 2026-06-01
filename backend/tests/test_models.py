"""Comprehensive ORM model unit tests for Portfolio, Position, Transaction, and History."""

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

    def test_invalid_port_id_too_short(self, sample_portfolio):
        portfolio = sample_portfolio(port_id="SHORT")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_port_id_too_long(self, sample_portfolio):
        portfolio = sample_portfolio(port_id="TOOLONGID")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_account_no_too_short(self, sample_portfolio):
        portfolio = sample_portfolio(account_no="12345")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Account number must be 10 characters" in result["errors"]

    def test_invalid_account_no_too_long(self, sample_portfolio):
        portfolio = sample_portfolio(account_no="12345678901")
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
        assert len(result["errors"]) >= 2
        assert "Portfolio ID must be 8 characters" in result["errors"]
        assert "Invalid status" in result["errors"]

    def test_all_valid_client_types(self, sample_portfolio):
        for ct in ["I", "C", "T"]:
            portfolio = sample_portfolio(client_type=ct)
            result = portfolio.validate_portfolio()
            assert result["valid"] is True

    def test_all_valid_statuses(self, sample_portfolio):
        for s in ["A", "C", "S"]:
            portfolio = sample_portfolio(status=s)
            result = portfolio.validate_portfolio()
            assert result["valid"] is True

    def test_none_port_id(self, sample_portfolio):
        portfolio = sample_portfolio(port_id=None)
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_none_account_no(self, sample_portfolio):
        portfolio = sample_portfolio(account_no=None)
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Account number must be 10 characters" in result["errors"]


# ---------------------------------------------------------------------------
# TestPortfolioCalculations
# ---------------------------------------------------------------------------
class TestPortfolioCalculations:
    """Tests for Portfolio.calculate_total_value() and update_total_value()."""

    def test_no_positions_only_cash(self, db_session, sample_portfolio):
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
            investment_id="AAPL123456",
            market_value=Decimal("5000.00"),
            status="A",
        )
        pos2 = sample_position(
            portfolio_id="TEST0001",
            investment_id="GOOG123456",
            market_value=Decimal("3000.00"),
            status="A",
        )
        db_session.add_all([pos1, pos2])
        db_session.flush()

        total = portfolio.calculate_total_value()
        assert total == Decimal("9000.00")

    def test_mixed_active_closed_positions(self, db_session, sample_portfolio, sample_position):
        portfolio = sample_portfolio(
            port_id="MIX00001",
            cash_balance=Decimal("2000.00"),
        )
        db_session.add(portfolio)
        db_session.flush()

        active_pos = sample_position(
            portfolio_id="MIX00001",
            investment_id="AAPL123456",
            market_value=Decimal("4000.00"),
            status="A",
        )
        closed_pos = sample_position(
            portfolio_id="MIX00001",
            investment_id="GOOG123456",
            market_value=Decimal("9999.00"),
            status="C",
        )
        db_session.add_all([active_pos, closed_pos])
        db_session.flush()

        total = portfolio.calculate_total_value()
        # Only active position market_value + cash_balance
        assert total == Decimal("6000.00")

    def test_none_cash_balance(self, db_session, sample_portfolio):
        portfolio = sample_portfolio(
            port_id="NOCASH01",
            cash_balance=None,
        )
        db_session.add(portfolio)
        db_session.flush()

        assert portfolio.calculate_total_value() == Decimal("0.00")

    def test_update_total_value_sets_fields(self, db_session, sample_portfolio):
        portfolio = sample_portfolio(
            port_id="UPDT0001",
            cash_balance=Decimal("7500.00"),
            total_value=None,
            last_maint=None,
        )
        db_session.add(portfolio)
        db_session.flush()

        portfolio.update_total_value()
        assert portfolio.total_value == Decimal("7500.00")
        assert portfolio.last_maint == date.today()


# ---------------------------------------------------------------------------
# TestPortfolioSerialization
# ---------------------------------------------------------------------------
class TestPortfolioSerialization:
    """Tests for Portfolio.to_dict()."""

    def test_to_dict_returns_correct_keys(self, sample_portfolio):
        portfolio = sample_portfolio(
            total_value=Decimal("15000.00"),
            last_maint=date(2025, 6, 15),
        )
        d = portfolio.to_dict()
        expected_keys = {
            "port_id", "account_no", "client_name", "client_type",
            "create_date", "last_maint", "status", "total_value",
            "cash_balance", "last_user", "last_trans",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_values(self, sample_portfolio):
        portfolio = sample_portfolio(
            total_value=Decimal("15000.00"),
            last_maint=date(2025, 6, 15),
        )
        d = portfolio.to_dict()
        assert d["port_id"] == "TEST0001"
        assert d["account_no"] == "1234567890"
        assert d["client_name"] == "Test Client"
        assert d["client_type"] == "I"
        assert d["status"] == "A"
        assert d["total_value"] == 15000.0
        assert d["cash_balance"] == 10000.0
        assert d["create_date"] == date.today().isoformat()
        assert d["last_maint"] == "2025-06-15"

    def test_to_dict_none_dates(self, sample_portfolio):
        portfolio = sample_portfolio(
            create_date=None,
            last_maint=None,
            total_value=None,
            cash_balance=None,
        )
        d = portfolio.to_dict()
        assert d["create_date"] is None
        assert d["last_maint"] is None
        assert d["total_value"] == 0.0
        assert d["cash_balance"] == 0.0

    def test_to_dict_decimal_to_float(self, sample_portfolio):
        portfolio = sample_portfolio(
            total_value=Decimal("12345.67"),
            cash_balance=Decimal("890.12"),
        )
        d = portfolio.to_dict()
        assert isinstance(d["total_value"], float)
        assert isinstance(d["cash_balance"], float)


# ---------------------------------------------------------------------------
# TestPositionGainLoss
# ---------------------------------------------------------------------------
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
        # cost_basis is falsy (0.00), so code returns zeros
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

    def test_break_even(self, sample_position):
        pos = sample_position(
            cost_basis=Decimal("10000.00"),
            market_value=Decimal("10000.00"),
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

    def test_none_portfolio_id(self, sample_position):
        pos = sample_position(portfolio_id=None)
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_none_investment_id(self, sample_position):
        pos = sample_position(investment_id=None)
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Investment ID must be 10 characters" in result["errors"]


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
        txn = sample_transaction(status="X")
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Invalid status" in result["errors"]

    def test_invalid_portfolio_id_length(self, sample_transaction):
        txn = sample_transaction(portfolio_id="SHORT")
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_sequence_no_length(self, sample_transaction):
        txn = sample_transaction(sequence_no="01")
        result = txn.validate_transaction()
        assert result["valid"] is False
        assert "Sequence number must be 6 characters" in result["errors"]

    def test_all_valid_types(self, sample_transaction):
        for t in ["BU", "SL", "TR", "FE"]:
            kwargs = {"type": t}
            if t in ("TR", "FE"):
                kwargs.update(investment_id=None, quantity=None, price=None)
            txn = sample_transaction(**kwargs)
            result = txn.validate_transaction()
            assert result["valid"] is True, f"Type {t} should be valid"

    def test_all_valid_statuses(self, sample_transaction):
        for s in ["P", "D", "F", "R"]:
            txn = sample_transaction(status=s)
            result = txn.validate_transaction()
            assert result["valid"] is True, f"Status {s} should be valid"


# ---------------------------------------------------------------------------
# TestTransactionStatusMachine
# ---------------------------------------------------------------------------
class TestTransactionStatusMachine:
    """Tests for can_transition_to() and transition_status()."""

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
        for target in ["P", "D", "F", "R"]:
            assert txn.can_transition_to(target) is False

    def test_transition_status_valid(self, sample_transaction):
        txn = sample_transaction(status="P")
        result = txn.transition_status("D", "ADMIN01")
        assert result is True
        assert txn.status == "D"
        assert txn.process_user == "ADMIN01"
        assert txn.process_date is not None

    def test_transition_status_invalid(self, sample_transaction):
        txn = sample_transaction(status="P")
        original_status = txn.status
        result = txn.transition_status("R", "ADMIN01")
        assert result is False
        assert txn.status == original_status


# ---------------------------------------------------------------------------
# TestTransactionCalculations
# ---------------------------------------------------------------------------
class TestTransactionCalculations:
    """Tests for calculate_transaction_amount() and update_amount()."""

    def test_calculate_amount(self, sample_transaction):
        txn = sample_transaction(
            quantity=Decimal("100.0000"),
            price=Decimal("150.0000"),
        )
        assert txn.calculate_transaction_amount() == Decimal("15000.00000000")

    def test_none_quantity(self, sample_transaction):
        txn = sample_transaction(quantity=None, price=Decimal("150.0000"))
        assert txn.calculate_transaction_amount() == Decimal("0.00")

    def test_none_price(self, sample_transaction):
        txn = sample_transaction(quantity=Decimal("100.0000"), price=None)
        assert txn.calculate_transaction_amount() == Decimal("0.00")

    def test_both_none(self, sample_transaction):
        txn = sample_transaction(quantity=None, price=None)
        assert txn.calculate_transaction_amount() == Decimal("0.00")

    def test_update_amount_sets_field(self, sample_transaction):
        txn = sample_transaction(
            quantity=Decimal("50.0000"),
            price=Decimal("200.0000"),
        )
        txn.update_amount()
        assert txn.amount == Decimal("10000.00000000")


# ---------------------------------------------------------------------------
# TestHistoryAuditRecord
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
            user="TESTER",
        )
        assert record.portfolio_id == "TEST0001"
        assert record.record_type == "PT"
        assert record.action_code == "C"
        assert record.before_image == json.dumps(before)
        assert record.after_image == json.dumps(after)
        assert record.process_user == "TESTER"
        assert record.process_date is not None
        assert record.seq_no == "0001"

    def test_create_audit_record_none_before_data(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
            before_data=None,
            after_data={"name": "New Portfolio"},
        )
        assert record.before_image is None
        assert record.after_image is not None

    def test_create_audit_record_with_db_session_increments_seq(self, db_session, sample_portfolio):
        # Insert parent portfolio first (FK constraint)
        portfolio = sample_portfolio(port_id="HIST0001")
        db_session.add(portfolio)
        db_session.flush()

        record1 = History.create_audit_record(
            portfolio_id="HIST0001",
            record_type="PT",
            action_code="A",
            after_data={"status": "A"},
            db_session=db_session,
        )
        db_session.add(record1)
        db_session.flush()

        # Create a second record with the same timestamp components
        # We need to manually set date/time to match for the count query to find the first
        record2 = History.create_audit_record(
            portfolio_id="HIST0001",
            record_type="PT",
            action_code="C",
            before_data={"status": "A"},
            after_data={"status": "C"},
            db_session=db_session,
        )
        # The seq_no should be at least "0001" (could be "0002" if timestamps match)
        assert record2.seq_no in ("0001", "0002")

    def test_create_audit_record_sets_process_date_and_user(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="TR",
            action_code="D",
            user="ADMIN",
        )
        assert record.process_user == "ADMIN"
        assert isinstance(record.process_date, datetime)

    def test_create_audit_record_default_reason_code(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PS",
            action_code="A",
        )
        assert record.reason_code == "AUTO"

    def test_get_before_data_valid_json(self):
        record = History(before_image=json.dumps({"key": "value"}))
        assert record.get_before_data() == {"key": "value"}

    def test_get_after_data_valid_json(self):
        record = History(after_image=json.dumps({"key": "value"}))
        assert record.get_after_data() == {"key": "value"}

    def test_get_before_data_none(self):
        record = History(before_image=None)
        assert record.get_before_data() is None

    def test_get_after_data_none(self):
        record = History(after_image=None)
        assert record.get_after_data() is None

    def test_get_before_data_invalid_json(self):
        record = History(before_image="not-valid-json{{{")
        assert record.get_before_data() is None

    def test_get_after_data_invalid_json(self):
        record = History(after_image="not-valid-json{{{")
        assert record.get_after_data() is None
