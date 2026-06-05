import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date, datetime, time
from models.database import Portfolio, Position
from models.transactions import Transaction
from models.history import History
from services.portfolio_service import PortfolioService


class TestProcessTransaction:

    def test_process_valid_buy_transaction(self, db_session, persisted_portfolio):
        txn = Transaction(
            date=date(2024, 6, 1),
            time=time(10, 30, 0),
            portfolio_id="TEST0001",
            sequence_no="000001",
            investment_id="AAPL123456",
            type="BU",
            quantity=Decimal("100.0000"),
            price=Decimal("150.0000"),
            amount=Decimal("15000.00"),
            currency="USD",
            status="P",
            process_user="TESTUSER",
        )
        db_session.add(txn)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(txn)
        assert result["success"] is True
        assert result["errors"] == []
        assert txn.status == "D"

    def test_process_invalid_transaction_returns_errors(self, db_session, persisted_portfolio):
        txn = Transaction(
            date=date(2024, 6, 1),
            time=time(10, 30, 0),
            portfolio_id=None,
            sequence_no="000001",
            type="BU",
            status="P",
            investment_id="AAPL123456",
            quantity=Decimal("100"),
            price=Decimal("150"),
        )
        service = PortfolioService(db_session)
        result = service.process_transaction(txn)
        assert result["success"] is False
        assert len(result["errors"]) > 0

    def test_process_fee_transaction(self, db_session, persisted_portfolio):
        txn = Transaction(
            date=date(2024, 6, 1),
            time=time(11, 0, 0),
            portfolio_id="TEST0001",
            sequence_no="000002",
            type="FE",
            quantity=None,
            price=None,
            amount=Decimal("50.00"),
            currency="USD",
            status="P",
            process_user="TESTUSER",
        )
        db_session.add(txn)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(txn)
        assert result["success"] is True

        portfolio = db_session.query(Portfolio).filter(
            Portfolio.port_id == "TEST0001"
        ).first()
        assert portfolio.cash_balance == Decimal("4950.00")

    def test_process_transfer_transaction(self, db_session, persisted_portfolio):
        txn = Transaction(
            date=date(2024, 6, 1),
            time=time(12, 0, 0),
            portfolio_id="TEST0001",
            sequence_no="000003",
            type="TR",
            quantity=None,
            price=None,
            amount=Decimal("1000.00"),
            currency="USD",
            status="P",
            process_user="TESTUSER",
        )
        db_session.add(txn)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(txn)
        assert result["success"] is True
        assert txn.status == "D"

    def test_process_sell_transaction(self, db_session, persisted_portfolio):
        pos = Position(
            portfolio_id="TEST0001",
            date=date(2024, 6, 1),
            investment_id="MSFT123456",
            quantity=Decimal("200.0000"),
            cost_basis=Decimal("30000.00"),
            market_value=Decimal("35000.00"),
            currency="USD",
            status="A",
            last_maint_date=datetime.now(),
            last_maint_user="TESTUSER",
        )
        db_session.add(pos)
        db_session.flush()

        txn = Transaction(
            date=date(2024, 6, 1),
            time=time(13, 0, 0),
            portfolio_id="TEST0001",
            sequence_no="000004",
            investment_id="MSFT123456",
            type="SL",
            quantity=Decimal("50.0000"),
            price=Decimal("175.0000"),
            amount=Decimal("8750.00"),
            currency="USD",
            status="P",
            process_user="TESTUSER",
        )
        db_session.add(txn)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(txn)
        assert result["success"] is True

        updated_pos = db_session.query(Position).filter(
            Position.portfolio_id == "TEST0001",
            Position.investment_id == "MSFT123456",
        ).first()
        assert updated_pos.quantity == Decimal("150.0000")

    def test_process_buy_creates_new_position(self, db_session, persisted_portfolio):
        txn = Transaction(
            date=date(2024, 6, 2),
            time=time(9, 0, 0),
            portfolio_id="TEST0001",
            sequence_no="000005",
            investment_id="GOOGL12345",
            type="BU",
            quantity=Decimal("50.0000"),
            price=Decimal("140.0000"),
            amount=Decimal("7000.00"),
            currency="USD",
            status="P",
            process_user="TESTUSER",
        )
        db_session.add(txn)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(txn)
        assert result["success"] is True

        new_pos = db_session.query(Position).filter(
            Position.portfolio_id == "TEST0001",
            Position.investment_id == "GOOGL12345",
        ).first()
        assert new_pos is not None
        assert new_pos.quantity == Decimal("50.0000")

    def test_process_transaction_exception_rolls_back(self, db_session, persisted_portfolio):
        txn = Transaction(
            date=date(2024, 6, 1),
            time=time(14, 0, 0),
            portfolio_id="TEST0001",
            sequence_no="000006",
            investment_id="FAIL123456",
            type="BU",
            quantity=Decimal("100"),
            price=Decimal("100"),
            amount=Decimal("10000.00"),
            currency="USD",
            status="P",
            process_user="TESTUSER",
        )
        db_session.add(txn)
        db_session.flush()

        service = PortfolioService(db_session)
        with patch.object(service, '_process_buy_sell_transaction', side_effect=Exception("DB error")):
            result = service.process_transaction(txn)
        assert result["success"] is False
        assert "DB error" in result["errors"][0]

    def test_fee_on_nonexistent_portfolio(self, db_session):
        txn = Transaction(
            date=date(2024, 6, 1),
            time=time(15, 0, 0),
            portfolio_id="NOEXIST1",
            sequence_no="000007",
            type="FE",
            amount=Decimal("50.00"),
            currency="USD",
            status="P",
            process_user="TESTUSER",
        )
        service = PortfolioService(db_session)
        result = service.process_transaction(txn)
        assert result["success"] is True
