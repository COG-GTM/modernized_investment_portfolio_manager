import pytest
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from models.database import Base, Portfolio, Position, get_db
from routers.portfolio import build_portfolio_summary

AS_OF = date(2026, 10, 28)


def _position(investment_id, quantity, cost_basis, market_value):
    return Position(
        portfolio_id="PF-22001",
        date=AS_OF,
        investment_id=investment_id,
        quantity=Decimal(quantity),
        cost_basis=Decimal(cost_basis),
        market_value=Decimal(market_value) if market_value is not None else None,
        currency="USD",
        status="A",
    )


@pytest.fixture
def portfolio():
    return Portfolio(
        port_id="PF-22001",
        account_no="2345678901",
        client_name="Sample Corporate Client",
        client_type="C",
        status="A",
        cash_balance=Decimal("18420.00"),
    )


@pytest.fixture
def client(portfolio):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    session.add(portfolio)
    session.add_all(
        [
            _position("AAPL", "400.0000", "68000.00", "74100.00"),
            _position("JPM", "250.0000", "48750.00", "55312.50"),
            _position("PVTCRD2031", "500000.0000", "500000.00", None),
        ]
    )
    session.commit()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    session.close()


def test_summary_with_unpriced_holding_does_not_raise(portfolio):
    positions = [
        _position("AAPL", "400.0000", "68000.00", "74100.00"),
        _position("PVTCRD2031", "500000.0000", "500000.00", None),
    ]

    summary = build_portfolio_summary(portfolio, positions)

    # Totals are computed over priced holdings only; the unpriced note is
    # surfaced as a null-valued holding rather than counted as a total loss.
    assert summary.totalValue == pytest.approx(74100.00 + 18420.00)
    assert summary.totalGainLoss == pytest.approx(6100.00)
    assert summary.totalGainLossPercent == pytest.approx(6100.00 / 68000.00 * 100, abs=0.01)
    unpriced = next(h for h in summary.holdings if h.symbol == "PVTCRD2031")
    assert unpriced.marketValue is None
    assert unpriced.gainLoss is None


def test_summary_with_only_unpriced_holdings(portfolio):
    summary = build_portfolio_summary(
        portfolio, [_position("PVTCRD2031", "500000.0000", "500000.00", None)]
    )

    assert summary.totalValue == pytest.approx(18420.00)
    assert summary.totalGainLoss == 0.0
    assert summary.totalGainLossPercent == 0.0


def test_get_portfolio_returns_200_when_a_holding_is_unpriced(client):
    response = client.get("/api/portfolio/2345678901")

    assert response.status_code == 200
    body = response.json()
    assert body["accountNumber"] == "2345678901"
    assert body["totalValue"] == pytest.approx(74100.00 + 55312.50 + 18420.00)
    assert body["totalGainLoss"] == pytest.approx(6100.00 + 6562.50)
    by_symbol = {h["symbol"]: h for h in body["holdings"]}
    assert by_symbol["PVTCRD2031"]["marketValue"] is None
    assert by_symbol["AAPL"]["marketValue"] == pytest.approx(74100.00)
