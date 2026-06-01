"""Comprehensive ORM model unit tests for Portfolio, Position, Transaction, and History."""

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

    def test_invalid_port_id_none(self, sample_portfolio):
        portfolio = sample_portfolio(port_id=None)
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Portfolio ID must be 8 characters" in result["errors"]

    def test_invalid_account_no_too_short(self, sample_portfolio):
        portfolio = sample_portfolio(account_no="12345")
        result = portfolio.validate_portfolio()
        assert result["valid"] is False
        assert "Account number must be 10 characters" in result["errors"]

    def test_invalid_account_no_none(self, sample_portfolio):
        portfolio = sample_portfolio(account_no=None)
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

    def test_all_valid_client_types(self, sample_portfolio):
        for ct in ["I", "C", "T"]:
            portfolio = sample_portfolio(client_type=ct)
            result = portfolio.validate_portfolio()
            assert result["valid"] is True

    def test_all_valid_statuses(self, sample_portfolio):
        for st in ["A", "C", "S"]:
            portfolio = sample_portfolio(status=st)
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
        assert total == Decimal("9000.00")  # 5000 + 3000 + 1000

    def test_mixed_active_and_closed_positions(self, db_session, sample_portfolio, sample_position):
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
            investment_id="GOOG123456",
            market_value=Decimal("6000.00"),
            status="C",
        )
        db_session.add_all([active_pos, closed_pos])
        db_session.flush()

        total = portfolio.calculate_total_value()
        # Only active position (4000) + cash (2000) = 6000; closed is excluded
        assert total == Decimal("6000.00")

    def test_none_cash_balance(self, db_session, sample_portfolio):
        portfolio = sample_portfolio(
            port_id="NONE0001",
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

    def test_returns_correct_keys_and_values(self, sample_portfolio):
        portfolio = sample_portfolio(
            total_value=Decimal("25000.00"),
            last_maint=date(2025, 6, 15),
            last_user="ADMIN01",
            last_trans="TR000001",
        )
        d = portfolio.to_dict()
        assert d["port_id"] == "TEST0001"
        assert d["account_no"] == "1234567890"
        assert d["client_name"] == "Test Client"
        assert d["client_type"] == "I"
        assert d["create_date"] == date.today().isoformat()
        assert d["last_maint"] == "2025-06-15"
        assert d["status"] == "A"
        assert d["total_value"] == 25000.0
        assert d["cash_balance"] == 10000.0
        assert d["last_user"] == "ADMIN01"
        assert d["last_trans"] == "TR000001"

    def test_handles_none_dates(self, sample_portfolio):
        portfolio = sample_portfolio(create_date=None, last_maint=None)
        d = portfolio.to_dict()
        assert d["create_date"] is None
        assert d["last_maint"] is None

    def test_converts_decimal_to_float(self, sample_portfolio):
        portfolio = sample_portfolio(
            total_value=Decimal("12345.67"),
            cash_balance=Decimal("9876.54"),
        )
        d = portfolio.to_dict()
        assert isinstance(d["total_value"], float)
        assert isinstance(d["cash_balance"], float)
        assert d["total_value"] == 12345.67
        assert d["cash_balance"] == 9876.54

    def test_none_total_value_and_cash_balance(self, sample_portfolio):
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
        # Zero cost_basis triggers the `not self.cost_basis` guard → returns zeros
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
        for st in ["A", "C", "P"]:
            pos = sample_position(status=st)
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
    """Tests for Transaction.can_transition_to() and transition_status()."""

    def test_p_to_d_allowed(self, sample_transaction):
        txn = sample_transaction(status="P")
        assert txn.can_transition_to("D") is True

    def test_p_to_f_allowed(self, sample_transaction):
        txn = sample_transaction(status="P")
        assert txn.can_transition_to("F") is True

    def test_p_to_r_not_allowed(self, sample_transaction):
        txn = sample_transaction(status="P")
        assert txn.can_transition_to("R") is False

    def test_d_to_r_allowed(self, sample_transaction):
        txn = sample_transaction(status="D")
        assert txn.can_transition_to("R") is True

    def test_d_to_p_not_allowed(self, sample_transaction):
        txn = sample_transaction(status="D")
        assert txn.can_transition_to("P") is False

    def test_f_to_p_retry_allowed(self, sample_transaction):
        txn = sample_transaction(status="F")
        assert txn.can_transition_to("P") is True

    def test_r_terminal_no_transitions(self, sample_transaction):
        txn = sample_transaction(status="R")
        for target in ["P", "D", "F", "R"]:
            assert txn.can_transition_to(target) is False

    def test_transition_status_valid(self, sample_transaction):
        txn = sample_transaction(status="P")
        result = txn.transition_status("D", "USER001")
        assert result is True
        assert txn.status == "D"
        assert txn.process_user == "USER001"
        assert txn.process_date is not None

    def test_transition_status_invalid_does_not_change(self, sample_transaction):
        txn = sample_transaction(status="P")
        original_status = txn.status
        result = txn.transition_status("R", "USER001")
        assert result is False
        assert txn.status == original_status


# ---------------------------------------------------------------------------
# TestTransactionCalculations
# ---------------------------------------------------------------------------

class TestTransactionCalculations:
    """Tests for Transaction.calculate_transaction_amount() and update_amount()."""

    def test_quantity_times_price(self, sample_transaction):
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

    def test_update_amount_sets_amount(self, sample_transaction):
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
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
            before_data={"status": "A"},
            after_data={"status": "C"},
            reason_code="MANU",
            user="ADMIN01",
        )
        assert record.portfolio_id == "TEST0001"
        assert record.record_type == "PT"
        assert record.action_code == "A"
        assert record.reason_code == "MANU"
        assert record.process_user == "ADMIN01"
        assert record.process_date is not None
        assert record.before_image == json.dumps({"status": "A"})
        assert record.after_image == json.dumps({"status": "C"})

    def test_create_audit_record_none_before_data(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
            before_data=None,
            after_data={"name": "New Client"},
        )
        assert record.before_image is None
        assert record.after_image is not None

    def test_create_audit_record_defaults(self):
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="TR",
            action_code="C",
        )
        assert record.reason_code == "AUTO"
        assert record.process_user == "SYSTEM"
        assert record.seq_no == "0001"

    def test_create_audit_record_with_db_session_increments_seq(self, db_session, sample_portfolio):
        # First add a parent portfolio so FK is satisfied
        portfolio = sample_portfolio(port_id="HIST0001")
        db_session.add(portfolio)
        db_session.flush()

        # Create first record and add to session
        rec1 = History.create_audit_record(
            portfolio_id="HIST0001",
            record_type="PT",
            action_code="A",
            db_session=db_session,
        )
        db_session.add(rec1)
        db_session.flush()

        # Create second record with same portfolio/date/time — seq_no should increment
        rec2 = History.create_audit_record(
            portfolio_id="HIST0001",
            record_type="PT",
            action_code="C",
            db_session=db_session,
        )
        # The seq_no should be "0001" or "0002" depending on timing.
        # Since both happen in the same second, the second should get "0002"
        assert rec2.seq_no in ("0001", "0002")
        # If same timestamp, must be greater than rec1
        if rec2.date == rec1.date and rec2.time == rec1.time:
            assert int(rec2.seq_no) > int(rec1.seq_no)

    def test_get_before_data_valid_json(self):
        h = History(before_image=json.dumps({"key": "value"}))
        assert h.get_before_data() == {"key": "value"}

    def test_get_after_data_valid_json(self):
        h = History(after_image=json.dumps({"key": "value"}))
        assert h.get_after_data() == {"key": "value"}

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

    def test_create_audit_record_serializes_complex_data(self):
        before = {"positions": [1, 2, 3], "nested": {"a": True}}
        after = {"positions": [1, 2, 3, 4], "nested": {"a": False}}
        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PS",
            action_code="C",
            before_data=before,
            after_data=after,
        )
        assert json.loads(record.before_image) == before
        assert json.loads(record.after_image) == after
