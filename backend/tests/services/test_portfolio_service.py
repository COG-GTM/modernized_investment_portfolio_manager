import pytest
from decimal import Decimal
from datetime import date, time, datetime
import uuid

from models.database import Portfolio, Position
from models.transactions import Transaction
from models.history import History
from services.portfolio_service import PortfolioService


def _unique_id():
    """Generate a short unique suffix for test PKs."""
    return uuid.uuid4().hex[:4].upper()


class TestProcessTransaction:

    def _make_portfolio(self, db_session, port_id, account_no):
        portfolio = Portfolio(
            port_id=port_id, account_no=account_no,
            client_name="Test Client", client_type="I",
            create_date=date.today(), status="A",
            cash_balance=Decimal("10000.00")
        )
        db_session.add(portfolio)
        db_session.flush()
        return portfolio

    def _make_buy_transaction(self, port_id, seq="000001"):
        t = Transaction(
            date=date.today(), time=time(9, 30),
            portfolio_id=port_id, sequence_no=seq,
            investment_id="AAPL123456", type="BU",
            quantity=Decimal("100.0000"), price=Decimal("150.0000"),
            currency="USD", status="P"
        )
        t.update_amount()
        return t

    def test_process_buy_transaction(self, db_session):
        uid = _unique_id()
        port_id = f"PRT{uid}A"[:8].ljust(8, "0")
        acct = f"10{uid}00000"[:10]
        self._make_portfolio(db_session, port_id, acct)
        transaction = self._make_buy_transaction(port_id)
        db_session.add(transaction)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(transaction)
        assert result["success"] is True
        assert result["errors"] == []

        position = db_session.query(Position).filter(
            Position.portfolio_id == port_id,
            Position.investment_id == "AAPL123456"
        ).first()
        assert position is not None
        assert position.quantity == Decimal("100.0000")
        assert position.status == "A"

    def test_process_invalid_transaction(self, db_session):
        uid = _unique_id()
        port_id = f"PRT{uid}B"[:8].ljust(8, "0")
        acct = f"20{uid}00000"[:10]
        self._make_portfolio(db_session, port_id, acct)
        t = Transaction(
            date=date.today(), time=time(9, 30),
            portfolio_id=port_id, sequence_no="000001",
            investment_id=None, type="BU",
            quantity=Decimal("100"), price=Decimal("150"),
            status="P"
        )
        service = PortfolioService(db_session)
        result = service.process_transaction(t)
        assert result["success"] is False
        assert len(result["errors"]) > 0

    def test_process_fee_transaction(self, db_session):
        uid = _unique_id()
        port_id = f"PRT{uid}C"[:8].ljust(8, "0")
        acct = f"30{uid}00000"[:10]
        portfolio = self._make_portfolio(db_session, port_id, acct)
        t = Transaction(
            date=date.today(), time=time(9, 30),
            portfolio_id=port_id, sequence_no="000002",
            type="FE", amount=Decimal("25.00"),
            status="P", currency="USD"
        )
        db_session.add(t)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(t)
        assert result["success"] is True

        db_session.refresh(portfolio)
        assert portfolio.cash_balance == Decimal("9975.00")

    def test_process_sell_transaction(self, db_session):
        uid = _unique_id()
        port_id = f"PRT{uid}D"[:8].ljust(8, "0")
        acct = f"40{uid}00000"[:10]
        self._make_portfolio(db_session, port_id, acct)

        pos = Position(
            portfolio_id=port_id, investment_id="AAPL123456",
            date=date.today(), quantity=Decimal("200.0000"),
            cost_basis=Decimal("30000.00"), market_value=Decimal("36000.00"),
            currency="USD", status="A"
        )
        db_session.add(pos)
        db_session.flush()

        t = Transaction(
            date=date.today(), time=time(10, 0),
            portfolio_id=port_id, sequence_no="000003",
            investment_id="AAPL123456", type="SL",
            quantity=Decimal("50.0000"), price=Decimal("180.0000"),
            amount=Decimal("9000.00"), currency="USD", status="P"
        )
        db_session.add(t)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(t)
        assert result["success"] is True

        db_session.refresh(pos)
        assert pos.quantity == Decimal("150.0000")

    def test_transaction_creates_audit_records(self, db_session):
        uid = _unique_id()
        port_id = f"PRT{uid}E"[:8].ljust(8, "0")
        acct = f"50{uid}00000"[:10]
        self._make_portfolio(db_session, port_id, acct)
        transaction = self._make_buy_transaction(port_id, seq="000010")
        db_session.add(transaction)
        db_session.flush()

        service = PortfolioService(db_session)
        service.process_transaction(transaction)

        history_records = db_session.query(History).filter(
            History.portfolio_id == port_id
        ).all()
        assert len(history_records) >= 1

    def test_transaction_status_changes_to_done(self, db_session):
        uid = _unique_id()
        port_id = f"PRT{uid}F"[:8].ljust(8, "0")
        acct = f"60{uid}00000"[:10]
        self._make_portfolio(db_session, port_id, acct)
        transaction = self._make_buy_transaction(port_id, seq="000020")
        db_session.add(transaction)
        db_session.flush()

        service = PortfolioService(db_session)
        service.process_transaction(transaction)
        assert transaction.status == "D"

    def test_transfer_transaction_noop(self, db_session):
        uid = _unique_id()
        port_id = f"PRT{uid}G"[:8].ljust(8, "0")
        acct = f"70{uid}00000"[:10]
        self._make_portfolio(db_session, port_id, acct)
        t = Transaction(
            date=date.today(), time=time(9, 30),
            portfolio_id=port_id, sequence_no="000030",
            type="TR", amount=Decimal("500.00"),
            status="P", currency="USD"
        )
        db_session.add(t)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(t)
        assert result["success"] is True
