from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401  registers every model on Base.metadata
from app.main import app
from models.database import Base, Portfolio, get_db
from models.esg import PortfolioEsgMetric


@pytest.fixture
def engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine):
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def client(engine):
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def _get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_portfolio(session, port_id="PF-12345", account_no="1234567890"):
    portfolio = Portfolio(
        port_id=port_id,
        account_no=account_no,
        client_name="Sample Client",
        client_type="I",
        create_date=date(2024, 1, 15),
        status="A",
        total_value=Decimal("125750.50"),
        cash_balance=Decimal("252.00"),
    )
    session.add(portfolio)
    session.commit()
    return portfolio


def make_metric(session, port_id="PF-12345", as_of_month="2026-10", computed_value="64.137484",
                coverage_pct="91.4804", positions_total=4):
    metric = PortfolioEsgMetric(
        port_id=port_id,
        as_of_month=as_of_month,
        computed_value=Decimal(computed_value) if computed_value is not None else None,
        coverage_pct=Decimal(coverage_pct),
        total_market_value=Decimal("125498.50") if positions_total else Decimal("0"),
        covered_market_value=Decimal("114806.50") if positions_total else Decimal("0"),
        positions_total=positions_total,
        positions_covered=3 if positions_total else 0,
        procedure_version="V001",
        computed_at=datetime(2026, 10, 29, 14, 5, 12),
    )
    session.add(metric)
    session.commit()
    return metric
