import pytest
from decimal import Decimal
from datetime import date, time, datetime

from models.database import Portfolio, Position
from models.transactions import Transaction
from models.history import History
from services.portfolio_service import PortfolioService


class TestProcessTransaction:

    def _make_portfolio(self, db_session):
        portfolio = Portfolio(
            port_id="PORT1234", account_no="1234567890",
            client_name="Test Client", client_type="I",
            create_date=date.today(), status="A",
            cash_balance=Decimal("10000.00")
        )
        db_session.add(portfolio)
        db_session.flush()
        return portfolio

    def _make_buy_transaction(self):
        t = Transaction(
            date=date.today(), time=time(9, 30),
            portfolio_id="PORT1234", sequence_no="000001",
            investment_id="AAPL123456", type="BU",
            quantity=Decimal("100.0000"), price=Decimal("150.0000"),
            currency="USD", status="P"
        )
        t.update_amount()
        return t

    def test_process_buy_transaction(self, db_session):
        self._make_portfolio(db_session)
        transaction = self._make_buy_transaction()
        db_session.add(transaction)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(transaction)
        assert result["success"] is True
        assert result["errors"] == []

        position = db_session.query(Position).filter(
            Position.portfolio_id == "PORT1234",
            Position.investment_id == "AAPL123456"
        ).first()
        assert position is not None
        assert position.quantity == Decimal("100.0000")
        assert position.status == "A"

    def test_process_invalid_transaction(self, db_session):
        self._make_portfolio(db_session)
        t = Transaction(
            date=date.today(), time=time(9, 30),
            portfolio_id="PORT1234", sequence_no="000001",
            investment_id=None, type="BU",
            quantity=Decimal("100"), price=Decimal("150"),
            status="P"
        )
        service = PortfolioService(db_session)
        result = service.process_transaction(t)
        assert result["success"] is False
        assert len(result["errors"]) > 0

    def test_process_fee_transaction(self, db_session):
        portfolio = self._make_portfolio(db_session)
        t = Transaction(
            date=date.today(), time=time(9, 30),
            portfolio_id="PORT1234", sequence_no="000002",
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
        self._make_portfolio(db_session)

        pos = Position(
            portfolio_id="PORT1234", investment_id="AAPL123456",
            date=date.today(), quantity=Decimal("200.0000"),
            cost_basis=Decimal("30000.00"), market_value=Decimal("36000.00"),
            currency="USD", status="A"
        )
        db_session.add(pos)
        db_session.flush()

        t = Transaction(
            date=date.today(), time=time(10, 0),
            portfolio_id="PORT1234", sequence_no="000003",
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
        self._make_portfolio(db_session)
        transaction = self._make_buy_transaction()
        db_session.add(transaction)
        db_session.flush()

        service = PortfolioService(db_session)
        service.process_transaction(transaction)

        history_records = db_session.query(History).filter(
            History.portfolio_id == "PORT1234"
        ).all()
        assert len(history_records) >= 1

    def test_transaction_status_changes_to_done(self, db_session):
        self._make_portfolio(db_session)
        transaction = self._make_buy_transaction()
        db_session.add(transaction)
        db_session.flush()

        service = PortfolioService(db_session)
        service.process_transaction(transaction)
        assert transaction.status == "D"

    def test_transfer_transaction_noop(self, db_session):
        self._make_portfolio(db_session)
        t = Transaction(
            date=date.today(), time=time(9, 30),
            portfolio_id="PORT1234", sequence_no="000004",
            type="TR", status="P", currency="USD"
        )
        db_session.add(t)
        db_session.flush()

        service = PortfolioService(db_session)
        result = service.process_transaction(t)
        assert result["success"] is True
