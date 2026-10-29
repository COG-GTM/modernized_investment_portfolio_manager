import pytest
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from models.database import Base, Portfolio, Position, get_db
from routers.portfolio import build_portfolio_summary


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(
        Portfolio(
            port_id="PF-22001",
            account_no="2345678901",
            client_name="Router Test",
            client_type="C",
            status="A",
            cash_balance=Decimal("1000.00"),
        )
    )
    session.add_all(
        [
            Position(
                portfolio_id="PF-22001",
                date=date(2026, 10, 28),
                investment_id="AAPL",
                quantity=Decimal("400.0000"),
                cost_basis=Decimal("68000.00"),
                market_value=Decimal("74100.00"),
                currency="USD",
                status="A",
            ),
            Position(
                portfolio_id="PF-22001",
                date=date(2026, 10, 28),
                investment_id="PVTCRD2031",
                quantity=Decimal("500000.0000"),
                cost_basis=Decimal("500000.00"),
                market_value=None,
                currency="USD",
                status="A",
            ),
        ]
    )
    session.commit()
    yield session
    session.close()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_summary_totals_skip_unpriced_holdings(db):
    portfolio = db.query(Portfolio).filter(Portfolio.account_no == "2345678901").one()
    positions = db.query(Position).order_by(Position.investment_id).all()

    summary = build_portfolio_summary(portfolio, positions)

    assert summary.totalValue == pytest.approx(75100.00)
    assert summary.totalGainLoss == pytest.approx(6100.00)
    assert summary.totalGainLossPercent == pytest.approx(8.97)
    unpriced = next(h for h in summary.holdings if h.symbol == "PVTCRD2031")
    assert unpriced.marketValue is None
    assert unpriced.gainLoss is None


def test_get_portfolio_returns_200_with_unpriced_holding(client):
    response = client.get("/api/portfolio/2345678901")

    assert response.status_code == 200
    body = response.json()
    assert body["accountNumber"] == "2345678901"
    assert len(body["holdings"]) == 2
    assert body["totalValue"] == pytest.approx(75100.00)
