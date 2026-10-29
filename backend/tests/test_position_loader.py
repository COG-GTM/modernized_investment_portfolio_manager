import pytest
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.database import Base, Portfolio, Position
from services.position_loader import find_latest_position_file, load_position_file

HEADER = "as_of_date,account_no,portfolio_id,investment_id,quantity,cost_basis,market_value,currency,status\n"


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(
        Portfolio(
            port_id="PF-00001",
            account_no="1111111111",
            client_name="Loader Test",
            client_type="I",
            status="A",
            cash_balance=Decimal("100.00"),
        )
    )
    session.commit()
    yield session
    session.close()


def write_file(tmp_path: Path, rows: str) -> Path:
    path = tmp_path / "positions_2026-10-28.csv"
    path.write_text(HEADER + rows)
    return path


def test_loads_rows_for_known_portfolio(db, tmp_path):
    path = write_file(
        tmp_path,
        "2026-10-28,1111111111,PF-00001,AAPL,10.0000,1500.00,1850.00,USD,A\n",
    )

    result = load_position_file(path, db)

    assert result.ok
    assert result.loaded == 1
    position = db.get(Position, ("PF-00001", date(2026, 10, 28), "AAPL"))
    assert position.market_value == Decimal("1850.00")
    assert position.last_maint_user == "NIGHTLY"


def test_replaying_the_same_file_does_not_duplicate(db, tmp_path):
    path = write_file(
        tmp_path,
        "2026-10-28,1111111111,PF-00001,AAPL,10.0000,1500.00,1850.00,USD,A\n",
    )

    load_position_file(path, db)
    load_position_file(path, db)

    assert db.query(Position).count() == 1


def test_unknown_portfolio_is_skipped_with_error(db, tmp_path):
    path = write_file(
        tmp_path,
        "2026-10-28,9999999999,PF-99999,AAPL,10.0000,1500.00,1850.00,USD,A\n",
    )

    result = load_position_file(path, db)

    assert result.loaded == 0
    assert result.skipped == 1
    assert "unknown portfolio" in result.errors[0]


def test_blank_market_value_defaults_to_zero(db, tmp_path):
    path = write_file(
        tmp_path,
        "2026-10-28,1111111111,PF-00001,PVTCRD2031,500000.0000,500000.00,,USD,A\n",
    )

    load_position_file(path, db)

    position = db.get(Position, ("PF-00001", date(2026, 10, 28), "PVTCRD2031"))
    assert position.market_value == Decimal("0.00")


def test_find_latest_position_file_picks_newest_folder(tmp_path):
    (tmp_path / "2026-10-27").mkdir()
    (tmp_path / "2026-10-28").mkdir()
    (tmp_path / "2026-10-27" / "positions_2026-10-27.csv").write_text(HEADER)
    newest = tmp_path / "2026-10-28" / "positions_2026-10-28.csv"
    newest.write_text(HEADER)

    assert find_latest_position_file(tmp_path) == newest
