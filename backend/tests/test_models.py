"""
Comprehensive ORM model unit tests.

Covers all model methods that currently have zero test coverage:
- Portfolio: validate_portfolio, calculate_total_value, update_total_value, to_dict
- Position: calculate_gain_loss, validate_position
- Transaction: validate_transaction, can_transition_to, transition_status,
               calculate_transaction_amount, update_amount
- History: create_audit_record, get_before_data, get_after_data

Run from the backend/ directory:
    cd backend && python -m pytest tests/ -v
"""

import json
import sys
import os
from decimal import Decimal
from datetime import date, time, datetime

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.database import Portfolio, Position
from models.transactions import Transaction
from models.history import History


# ---------------------------------------------------------------------------
# Portfolio validation
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


# ---------------------------------------------------------------------------
# Portfolio calculations
# ---------------------------------------------------------------------------


class TestPortfolioCalculations:
    """Tests for Portfolio.calculate_total_value() and update_total_value()."""

    def test_no_positions_only_cash(self, db_session, sample_portfolio):
        portfolio = sample_portfolio(cash_balance=Decimal("10000.00"))
        db_session.add(portfolio)
        db_session.flush()

        total = portfolio.calculate_total_value()
        assert total == Decimal("10000.00")

    def test_with_active_positions(self, db_session, sample_portfolio, sample_position):
        portfolio = sample_portfolio(cash_balance=Decimal("5000.00"))
        db_session.add(portfolio)
        db_session.flush()

        pos1 = sample_position(
            portfolio_id="TEST0001",
            investment_id="AAPL123456",
            date=date(2024, 1, 1),
            market_value=Decimal("10000.00"),
            status="A",
        )
        pos2 = sample_position(
            portfolio_id="TEST0001",
            investment_id="GOOG123456",
            date=date(2024, 1, 1),
            market_value=Decimal("20000.00"),
            status="A",
        )
        db_session.add_all([pos1, pos2])
        db_session.flush()

        total = portfolio.calculate_total_value()
        assert total == Decimal("35000.00")

    def test_mixed_active_closed_positions(self, db_session, sample_portfolio, sample_position):
        portfolio = sample_portfolio(cash_balance=Decimal("5000.00"))
        db_session.add(portfolio)
        db_session.flush()

        active = sample_position(
            portfolio_id="TEST0001",
            investment_id="AAPL123456",
            date=date(2024, 2, 1),
            market_value=Decimal("10000.00"),
            status="A",
        )
        closed = sample_position(
            portfolio_id="TEST0001",
            investment_id="GOOG123456",
            date=date(2024, 2, 1),
            market_value=Decimal("20000.00"),
            status="C",
        )
        db_session.add_all([active, closed])
        db_session.flush()

        total = portfolio.calculate_total_value()
        # Only active position counted
        assert total == Decimal("15000.00")

    def test_none_cash_balance(self, db_session, sample_portfolio):
        portfolio = sample_portfolio(cash_balance=None)
        db_session.add(portfolio)
        db_session.flush()

        total = portfolio.calculate_total_value()
        assert total == Decimal("0.00")

    def test_update_total_value(self, db_session, sample_portfolio):
        portfolio = sample_portfolio(cash_balance=Decimal("7500.00"))
        db_session.add(portfolio)
        db_session.flush()

        portfolio.update_total_value()
        assert portfolio.total_value == Decimal("7500.00")
        assert portfolio.last_maint == date.today()


# ---------------------------------------------------------------------------
# Portfolio serialization
# ---------------------------------------------------------------------------


class TestPortfolioSerialization:
    """Tests for Portfolio.to_dict()."""

    def test_to_dict_keys_and_values(self, sample_portfolio):
        portfolio = sample_portfolio(
            total_value=Decimal("25000.00"),
            cash_balance=Decimal("10000.00"),
            create_date=date(2024, 1, 15),
            last_maint=date(2024, 6, 1),
            last_user="ADMIN01",
            last_trans="TR000001",
        )
        d = portfolio.to_dict()
        assert d["port_id"] == "TEST0001"
        assert d["account_no"] == "1234567890"
        assert d["client_name"] == "Test Client"
        assert d["client_type"] == "I"
        assert d["create_date"] == "2024-01-15"
        assert d["last_maint"] == "2024-06-01"
        assert d["status"] == "A"
        assert d["total_value"] == 25000.0
        assert d["cash_balance"] == 10000.0
        assert d["last_user"] == "ADMIN01"
        assert d["last_trans"] == "TR000001"

    def test_to_dict_none_dates(self, sample_portfolio):
        portfolio = sample_portfolio(create_date=None, last_maint=None, total_value=None, cash_balance=None)
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
        # zero cost_basis is falsy for Decimal('0'), so treated as no data
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
        pos = sample_position(quantity=Decimal("-50"))
        result = pos.validate_position()
        assert result["valid"] is False
        assert "Quantity cannot be negative" in result["errors"]


# ---------------------------------------------------------------------------
# Transaction validation
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
        txn = sample_transaction(type="SL", price=Decimal("-5"))
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
# Transaction status machine
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

    def test_f_to_p_allowed_retry(self, sample_transaction):
        txn = sample_transaction(status="F")
        assert txn.can_transition_to("P") is True

    def test_r_terminal_state(self, sample_transaction):
        txn = sample_transaction(status="R")
        assert txn.can_transition_to("P") is False
        assert txn.can_transition_to("D") is False
        assert txn.can_transition_to("F") is False
        assert txn.can_transition_to("R") is False

    def test_transition_status_valid(self, sample_transaction):
        txn = sample_transaction(status="P")
        result = txn.transition_status("D", "ADMIN01")
        assert result is True
        assert txn.status == "D"
        assert txn.process_user == "ADMIN01"
        assert isinstance(txn.process_date, datetime)

    def test_transition_status_invalid(self, sample_transaction):
        txn = sample_transaction(status="P")
        original_status = txn.status
        result = txn.transition_status("R", "ADMIN01")
        assert result is False
        assert txn.status == original_status


# ---------------------------------------------------------------------------
# Transaction calculations
# ---------------------------------------------------------------------------


class TestTransactionCalculations:
    """Tests for Transaction.calculate_transaction_amount() and update_amount()."""

    def test_calculate_amount(self, sample_transaction):
        txn = sample_transaction(quantity=Decimal("100.0000"), price=Decimal("150.0000"))
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

    def test_update_amount(self, sample_transaction):
        txn = sample_transaction(quantity=Decimal("50.0000"), price=Decimal("200.0000"))
        txn.update_amount()
        assert txn.amount == Decimal("10000.00000000")


# ---------------------------------------------------------------------------
# History audit record
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
        assert record.reason_code == "AUTO"
        assert record.process_user == "SYSTEM"
        assert isinstance(record.process_date, datetime)

    def test_create_audit_record_with_data(self):
        before = {"status": "A", "cash_balance": 10000}
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

    def test_create_audit_record_with_db_session(self, db_session, sample_portfolio):
        # Add a parent portfolio so FK constraint is satisfied
        portfolio = sample_portfolio()
        db_session.add(portfolio)
        db_session.flush()

        record = History.create_audit_record(
            portfolio_id="TEST0001",
            record_type="PT",
            action_code="A",
            db_session=db_session,
        )
        assert record.seq_no == "0001"

    def test_get_before_data_valid_json(self):
        h = History(
            portfolio_id="TEST0001",
            date="20240101",
            time="12000000",
            seq_no="0001",
            before_image='{"key": "value"}',
        )
        result = h.get_before_data()
        assert result == {"key": "value"}

    def test_get_before_data_none(self):
        h = History(
            portfolio_id="TEST0001",
            date="20240101",
            time="12000000",
            seq_no="0001",
            before_image=None,
        )
        assert h.get_before_data() is None

    def test_get_before_data_invalid_json(self):
        h = History(
            portfolio_id="TEST0001",
            date="20240101",
            time="12000000",
            seq_no="0001",
            before_image="not-valid-json{",
        )
        assert h.get_before_data() is None

    def test_get_after_data_valid_json(self):
        h = History(
            portfolio_id="TEST0001",
            date="20240101",
            time="12000000",
            seq_no="0001",
            after_image='{"status": "C"}',
        )
        result = h.get_after_data()
        assert result == {"status": "C"}

    def test_get_after_data_none(self):
        h = History(
            portfolio_id="TEST0001",
            date="20240101",
            time="12000000",
            seq_no="0001",
            after_image=None,
        )
        assert h.get_after_data() is None

    def test_get_after_data_invalid_json(self):
        h = History(
            portfolio_id="TEST0001",
            date="20240101",
            time="12000000",
            seq_no="0001",
            after_image="{{invalid}}",
        )
        assert h.get_after_data() is None
