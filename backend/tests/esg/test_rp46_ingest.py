"""RP-46: Ingest monthly ESG feed from inbound bucket into staging."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from tests.esg.conftest import (
    AS_OF_MONTH,
    FEED_2026_10,
    FEED_2026_10_SHORT_ROWS,
    FEED_2026_10_WITH_REJECTS,
    FEED_2026_11,
    REJECTS_TABLE,
    STAGING_TABLE,
    EsgDb,
    field,
)

esg_service = pytest.importorskip(
    "services.esg_service",
    reason="RP-46: backend/services/esg_service.py is not implemented yet",
)

pytestmark = [pytest.mark.esg, pytest.mark.rp46]


@pytest.fixture
def inbound(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Local stand-in for the inbound bucket with the S3-compatible layout esg/<month>/<file>."""
    root = tmp_path / "inbound"
    for src in (FEED_2026_10, FEED_2026_10_WITH_REJECTS, FEED_2026_10_SHORT_ROWS, FEED_2026_11):
        dest = root / "esg" / src.parent.name / src.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest)
    monkeypatch.setenv("ESG_INBOUND_DIR", str(root))
    return root


def _load(path: Path):
    return esg_service.load_feed(str(path))


def test_rp46_01_loader_contract_exposes_load_feed_and_load_result():
    """RP-46 AC: loader is callable as load_feed(path) and returns a LoadResult."""
    assert callable(getattr(esg_service, "load_feed", None))
    assert hasattr(esg_service, "LoadResult")


def test_rp46_02_clean_file_lands_in_staging_with_batch_id(esg_db: EsgDb, inbound: Path):
    """RP-46 AC: loader copies the CSV into stg_esg_emissions with a load batch id."""
    esg_db.require_table(STAGING_TABLE, "RP-46")
    result = _load(inbound / "esg" / "2026-10" / "esg_emissions_2026-10.csv")

    batch_id = field(result, "batch_id", "load_batch_id")
    assert batch_id, "LoadResult must expose the load batch id"
    assert field(result, "rows_loaded", "loaded", "loaded_rows", "inserted") == 5
    assert field(result, "rows_rejected", "rejected", "rejected_rows", default=0) == 0

    rows = esg_db.rows(f"SELECT * FROM {STAGING_TABLE} WHERE as_of_month = :m", m=AS_OF_MONTH)
    assert len(rows) == 5
    assert {r["investment_id"] for r in rows} == {
        "INV0000001", "INV0000002", "INV0000003", "INV0000004", "INV0000009"
    }
    assert {r["load_batch_id"] for r in rows} == {batch_id}


def test_rp46_03_staging_preserves_numeric_values_and_blank_revenue(esg_db: EsgDb, inbound: Path):
    """RP-46 AC: staged values equal the CSV values; a blank revenue is stored as NULL, not 0."""
    _load(inbound / "esg" / "2026-10" / "esg_emissions_2026-10.csv")
    row = esg_db.rows(
        f"SELECT * FROM {STAGING_TABLE} WHERE as_of_month = :m AND investment_id = 'INV0000001'", m=AS_OF_MONTH
    )[0]
    assert float(row["scope1_tco2e"]) == pytest.approx(120.0)
    assert float(row["scope2_tco2e"]) == pytest.approx(80.0)
    assert float(row["revenue_musd"]) == pytest.approx(50.0)

    blank = esg_db.rows(
        f"SELECT revenue_musd FROM {STAGING_TABLE} WHERE as_of_month = :m AND investment_id = 'INV0000003'",
        m=AS_OF_MONTH,
    )[0]
    assert blank["revenue_musd"] is None


def test_rp46_04_rerunning_same_file_does_not_duplicate_rows(esg_db: EsgDb, inbound: Path):
    """RP-46 AC: re-running the same file must not duplicate rows."""
    path = inbound / "esg" / "2026-10" / "esg_emissions_2026-10.csv"
    _load(path)
    first = esg_db.count(STAGING_TABLE, "as_of_month = :m", m=AS_OF_MONTH)
    second_result = _load(path)
    second = esg_db.count(STAGING_TABLE, "as_of_month = :m", m=AS_OF_MONTH)

    assert first == 5
    assert second == first
    assert field(second_result, "rows_loaded", "loaded", "loaded_rows", "inserted", default=0) in (0, 5)
    per_investment = esg_db.rows(
        f"SELECT investment_id, COUNT(*) AS n FROM {STAGING_TABLE} WHERE as_of_month = :m "
        "GROUP BY investment_id HAVING COUNT(*) > 1",
        m=AS_OF_MONTH,
    )
    assert per_investment == []


def test_rp46_05_rerun_does_not_duplicate_rejects_either(esg_db: EsgDb, inbound: Path):
    """RP-46 AC (edge): re-running a file with malformed rows must not duplicate reject rows."""
    esg_db.require_table(REJECTS_TABLE, "RP-46")
    path = inbound / "esg" / "2026-10" / "esg_emissions_2026-10_with_rejects.csv"
    _load(path)
    first = esg_db.count(REJECTS_TABLE)
    _load(path)
    assert esg_db.count(REJECTS_TABLE) == first == 5


def test_rp46_06_malformed_rows_go_to_rejects_with_reason(esg_db: EsgDb, inbound: Path):
    """RP-46 AC: malformed rows go to a rejects table with a reason; good rows still load."""
    esg_db.require_table(REJECTS_TABLE, "RP-46")
    result = _load(inbound / "esg" / "2026-10" / "esg_emissions_2026-10_with_rejects.csv")

    assert field(result, "rows_loaded", "loaded", "loaded_rows", "inserted") == 2
    assert field(result, "rows_rejected", "rejected", "rejected_rows") == 5
    assert esg_db.count(STAGING_TABLE, "as_of_month = :m", m=AS_OF_MONTH) == 2

    rejects = esg_db.rows(f"SELECT * FROM {REJECTS_TABLE}")
    assert len(rejects) == 5
    reason_col = next((c for c in rejects[0] if "reason" in c.lower()), None)
    assert reason_col, "rejects table must carry a reason column"
    assert all(str(r[reason_col]).strip() for r in rejects), "every reject needs a non-empty reason"
    batch_col = next((c for c in rejects[0] if "batch" in c.lower()), None)
    assert batch_col, "rejects must be tied to the load batch"


def test_rp46_07_negative_emissions_are_rejected(esg_db: EsgDb, inbound: Path):
    """RP-46 / RP-52 AC: a row with negative scope emissions is rejected and never staged."""
    esg_db.require_table(REJECTS_TABLE, "RP-46")
    _load(inbound / "esg" / "2026-10" / "esg_emissions_2026-10_with_rejects.csv")

    staged = esg_db.rows(f"SELECT investment_id FROM {STAGING_TABLE} WHERE investment_id = 'INV0000005'")
    assert staged == [], "negative scope1 row must not reach staging"
    rejected = esg_db.rows(f"SELECT * FROM {REJECTS_TABLE}")
    joined = " ".join(str(v) for r in rejected for v in r.values()).lower()
    assert "inv0000005" in joined
    assert "negative" in joined or "< 0" in joined or "non-negative" in joined


def test_rp46_08_negative_revenue_is_rejected(esg_db: EsgDb, inbound: Path):
    """RP-46 AC (edge): negative revenue is malformed and goes to rejects."""
    _load(inbound / "esg" / "2026-10" / "esg_emissions_2026-10_with_rejects.csv")
    assert esg_db.count(STAGING_TABLE, "investment_id = 'INV0000008'") == 0


def test_rp46_09_invalid_month_and_missing_investment_id_are_rejected(esg_db: EsgDb, inbound: Path):
    """RP-46 AC (edge): invalid as_of_month and blank investment_id are malformed."""
    _load(inbound / "esg" / "2026-10" / "esg_emissions_2026-10_with_rejects.csv")
    assert esg_db.count(STAGING_TABLE, "as_of_month = '2026-13'") == 0
    assert esg_db.count(STAGING_TABLE, "investment_id IS NULL OR investment_id = ''") == 0


def test_rp46_10_short_row_is_rejected_not_fatal(esg_db: EsgDb, inbound: Path):
    """RP-46 AC (edge): a row with too few columns is rejected; the loader does not abort."""
    result = _load(inbound / "esg" / "2026-10" / "esg_emissions_2026-10_short_rows.csv")
    assert field(result, "rows_loaded", "loaded", "loaded_rows", "inserted") == 1
    assert field(result, "rows_rejected", "rejected", "rejected_rows") == 1


def test_rp46_11_missing_file_raises_clear_error(esg_db: EsgDb, inbound: Path):
    """RP-46 AC (edge): a path that does not exist raises FileNotFoundError rather than loading nothing silently."""
    with pytest.raises((FileNotFoundError, OSError, ValueError)):
        _load(inbound / "esg" / "2026-09" / "esg_emissions_2026-09.csv")


def test_rp46_12_each_run_gets_its_own_batch_id(esg_db: EsgDb, inbound: Path):
    """RP-46 AC (edge): two different files produce two different load batch ids."""
    a = _load(inbound / "esg" / "2026-10" / "esg_emissions_2026-10.csv")
    b = _load(inbound / "esg" / "2026-11" / "esg_emissions_2026-11.csv")
    assert field(a, "batch_id", "load_batch_id") != field(b, "batch_id", "load_batch_id")
    assert esg_db.count(STAGING_TABLE, "as_of_month = '2026-11'") == 3
