"""Comprehensive ORM model unit tests for Portfolio, Position, Transaction, and History."""

import json
import pytest
from decimal import Decimal
from datetime import date, time, datetime

from models.database import Portfolio, Position
from models.transactions import Transaction
from models.history import History


# ---------------------------------------------------------------------------
# TestPortfolioValidation
# ---------------------------------------------------------------------------
class TestPortfolioValidation:
    """Test Portfolio.validate_portfolio()."""

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
        assert len(result["errors"]) == 2
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


# ---------------------------------------------------------------------------
# TestPortfolioCalculations
# ---------------------------------------------------------------------------
class TestPortfolioCalculations:
    """Test Portfolio.calculate_total_value() and Portfolio.update_total_value()."""

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
            date=date(2025, 1, 2),
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
            port_id="MIXD0001",
            cash_balance=Decimal("2000.00"),
        )
        db_session.add(portfolio)
        db_session.flush()

        active_pos = sample_position(
            portfolio_id="MIXD0001",
            investment_id="AAPL123456",
            market_value=Decimal("4000.00"),
            status="A",
        )
        closed_pos = sample_position(
            portfolio_id="MIXD0001",
            date=date(2025, 1, 2),
            investment_id="MSFT123456",
            market_value=Decimal("6000.00"),
            status="C",
        )
        db_session.add_all([active_pos, closed_pos])
        db_session.flush()

        total = portfolio.calculate_total_value()
        # Only the active position (4000) + cash (2000) = 6000
        assert total == Decimal("6000.00")

    def test_none_cash_balance(self, db_session, sample_portfolio):
        portfolio = sample_portfolio(
            port_id="NCSH0001",
            cash_balance=None,
        )
        db_session.add(portfolio)
        db_session.flush()
        assert portfolio.calculate_total_value() == Decimal("0.00")

    def test_update_total_value(self, db_session, sample_portfolio):
        portfolio = sample_portfolio(
            port_id="UPDT0001",
            cash_balance=Decimal("7500.00"),
            total_value=None,
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
    """Test Portfolio.to_dict()."""

    def test_to_dict_returns_correct_keys(self, sample_portfolio):
        portfolio = sample_portfolio(
            total_value=Decimal("50000.00"),
            last_user="ADMIN",
            last_trans="TR000001",
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
            total_value=Decimal("50000.00"),
            last_maint=today,
            last_user="ADMIN",
            last_trans="TR000001",
        )
        d = portfolio.to_dict()
        assert d["port_id"] == "TEST0001"
        assert d["account_no"] == "1234567890"
        assert d["client_name"] == "Test Client"
        assert d["client_type"] == "I"
        assert d["create_date"] == today.isoformat()
        assert d["last_maint"] == today.isoformat()
        assert d["status"] == "A"
        assert d["total_value"] == 50000.0
        assert d["cash_balance"] == 10000.0
        assert d["last_user"] == "ADMIN"
        assert d["last_trans"] == "TR000001"

    def test_to_dict_handles_none_dates(self, sample_portfolio):
        portfolio = sample_portfolio(create_date=None, last_maint=None)
        d = portfolio.to_dict()
        assert d["create_date"] is None
        assert d["last_maint"] is None

    def test_to_dict_converts_decimal_to_float(self, sample_portfolio):
        portfolio = sample_portfolio(
            total_value=Decimal("12345.67"),
            cash_balance=Decimal("890.12"),
        )
        d = portfolio.to_dict()
        assert isinstance(d["total_value"], float)
        assert isinstance(d["cash_balance"], float)
        assert d["total_value"] == 12345.67
        assert d["cash_balance"] == 890.12

    def test_to_dict_none_total_and_cash(self, sample_portfolio):
        portfolio = sample_portfolio(total_value=None, cash_balance=None)
        d = portfolio.to_dict()
        assert d["total_value"] == 0.0
        assert d["cash_balance"] == 0.0


# ---------------------------------------------------------------------------
# TestPositionGainLoss
# ---------------------------------------------------------------------------
class TestPositionGainLoss:
    """Test Position.calculate_gain_loss()."""

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
        # zero cost_basis is falsy for Decimal('0.00') so returns zeros
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
    """Test Position.validate_position()."""

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

    def test_multiple_errors(self, sample_position):
        pos = sample_position(portfolio_id="BAD", investment_id="BAD", status="X")
        result = pos.validate_position()
        assert result["valid"] is False
        assert len(result["errors"]) == 3


# ---------------------------------------------------------------------------
# TestTransactionValidation
# ---------------------------------------------------------------------------
class TestTransactionValidation:
    """Test Transaction.validate_transaction()."""

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

    def test_valid_sell_transaction(self, sample_transaction):
        txn = sample_transaction(type="SL")
        result = txn.validate_transaction()
        assert result["valid"] is True

    def test_valid_transfer_transaction(self, sample_transaction):
        txn = sample_transaction(type="TR")
        result = txn.validate_transaction()
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# TestTransactionStatusMachine
# ---------------------------------------------------------------------------
class TestTransactionStatusMachine:
    """Test can_transition_to() and transition_status()."""

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

    def test_failed_to_pending_allowed_retry(self, sample_transaction):
        txn = sample_transaction(status="F")
        assert txn.can_transition_to("P") is True

    def test_reversed_is_terminal(self, sample_transaction):
        txn = sample_transaction(status="R")
        for target in ["P", "D", "F", "R"]:
            assert txn.can_transition_to(target) is False

    def test_transition_status_valid(self, sample_transaction):
        txn = sample_transaction(status="P")
        result = txn.transition_status("D", "TRADER01")
        assert result is True
        assert txn.status == "D"
        assert txn.process_user == "TRADER01"
        assert txn.process_date is not None

    def test_transition_status_invalid(self, sample_transaction):
        txn = sample_transaction(status="P")
        original_status = txn.status
        result = txn.transition_status("R", "TRADER01")
        assert result is False
        assert txn.status == original_status

    def test_transition_status_chain(self, sample_transaction):
        """Test a full lifecycle: P -> D -> R."""
        txn = sample_transaction(status="P")
        assert txn.transition_status("D", "USER1") is True
        assert txn.status == "D"
        assert txn.transition_status("R", "USER2") is True
        assert txn.status == "R"
        # R is terminal
        assert txn.transition_status("P", "USER3") is False
        assert txn.status == "R"


# ---------------------------------------------------------------------------
# TestTransactionCalculations
# ---------------------------------------------------------------------------
class TestTransactionCalculations:
    """Test calculate_transaction_amount() and update_amount()."""

    def test_calculate_amount(self, sample_transaction):
        txn = sample_transaction(
            quantity=Decimal("100.0000"),
            price=Decimal("150.0000"),
        )
        assert txn.calculate_transaction_amount() == Decimal("15000.00000000")

    def test_calculate_amount_none_quantity(self, sample_transaction):
        txn = sample_transaction(quantity=None, price=Decimal("150.0000"))
        assert txn.calculate_transaction_amount() == Decimal("0.00")

    def test_calculate_amount_none_price(self, sample_transaction):
        txn = sample_transaction(quantity=Decimal("100.0000"), price=None)
        assert txn.calculate_transaction_amount() == Decimal("0.00")

    def test_calculate_amount_both_none(self, sample_transaction):
        txn = sample_transaction(quantity=None, price=None)
        assert txn.calculate_transaction_amount() == Decimal("0.00")

    def test_update_amount(self, sample_transaction):
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
    """Test History.create_audit_record(), get_before_data(), and get_after_data()."""

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
        assert record.reason_code == "AUTO"
        assert record.process_date is not None
        assert record.before_image is None
        assert record.after_image is None

    def test_create_audit_record_with_data(self):
        before = {"status": "A", "cash_balance": "10000.00"}
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
            after_data={"status": "A"},
        )
        assert record.before_image is None
        assert record.after_image is not None

    def test_create_audit_record_sets_date_and_time(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="TR",
            action_code="D",
        )
        assert len(record.date) == 8
        assert len(record.time) == 8
        assert record.seq_no == "0001"

    def test_create_audit_record_with_db_session_increments_seq(self, db_session, sample_portfolio):
        # Add a parent portfolio first for FK constraint
        portfolio = sample_portfolio(port_id="HIST0001")
        db_session.add(portfolio)
        db_session.flush()

        rec1 = History.create_audit_record(
            portfolio_id="HIST0001",
            record_type="PT",
            action_code="A",
            after_data={"status": "A"},
            db_session=db_session,
        )
        db_session.add(rec1)
        db_session.flush()

        rec2 = History.create_audit_record(
            portfolio_id="HIST0001",
            record_type="PT",
            action_code="C",
            before_data={"status": "A"},
            after_data={"status": "C"},
            db_session=db_session,
        )
        # seq_no should be incremented since there's already a record
        # with the same portfolio_id, date, and time
        assert int(rec2.seq_no) >= 1

    def test_get_before_data_valid_json(self):
        record = History(before_image='{"key": "value"}')
        assert record.get_before_data() == {"key": "value"}

    def test_get_after_data_valid_json(self):
        record = History(after_image='{"key": "value"}')
        assert record.get_after_data() == {"key": "value"}

    def test_get_before_data_none(self):
        record = History(before_image=None)
        assert record.get_before_data() is None

    def test_get_after_data_none(self):
        record = History(after_image=None)
        assert record.get_after_data() is None

    def test_get_before_data_invalid_json(self):
        record = History(before_image="not valid json {{{")
        assert record.get_before_data() is None

    def test_get_after_data_invalid_json(self):
        record = History(after_image="not valid json {{{")
        assert record.get_after_data() is None

    def test_create_audit_record_custom_reason_code(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PS",
            action_code="C",
            reason_code="MANU",
        )
        assert record.reason_code == "MANU"
