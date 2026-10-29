"""RP-46 loader tests: staging, rejects, idempotent re-run."""
import pytest

from models.esg import EsgLoadBatch, EsgLoadReject, StgEsgEmissions
from services.esg_service import EsgFeedError, load_esg_feed
from tests.esg.conftest import SAMPLE_FEED, AS_OF, write_feed


def test_sample_feed_stages_valid_rows_and_rejects_malformed(db):
    result = load_esg_feed(db, SAMPLE_FEED)

    assert result.skipped is False
    assert result.as_of_months == [AS_OF]
    assert result.loaded_rows == 3
    assert result.rejected_rows == 2

    staged = {row.investment_id: row for row in db.query(StgEsgEmissions).all()}
    assert set(staged) == {"AAPL", "MSFT", "GOOGL"}
    assert all(row.load_batch_id == result.batch_id for row in staged.values())
    assert float(staged["AAPL"].revenue_musd) == pytest.approx(391035)

    rejects = {row.source_row_no: row.reason for row in db.query(EsgLoadReject).all()}
    assert rejects == {5: "revenue_musd missing", 6: "scope1_tco2e must be >= 0, got -1200"}

    batch = db.query(EsgLoadBatch).one()
    assert batch.file_name == SAMPLE_FEED.name
    assert batch.loaded_rows == 3 and batch.rejected_rows == 2 and batch.as_of_month == AS_OF


def test_rerunning_same_file_does_not_duplicate_rows(db):
    first = load_esg_feed(db, SAMPLE_FEED)
    second = load_esg_feed(db, SAMPLE_FEED)

    assert second.skipped is True
    assert second.batch_id == first.batch_id
    assert second.as_of_months == [AS_OF]
    assert db.query(StgEsgEmissions).count() == 3
    assert db.query(EsgLoadReject).count() == 2
    assert db.query(EsgLoadBatch).count() == 1


def test_corrected_resend_replaces_staging_row_instead_of_duplicating(db, tmp_path):
    load_esg_feed(db, write_feed(tmp_path, ["2026-10,AAPL,100,50,1000"], name="v1.csv"))
    result = load_esg_feed(db, write_feed(tmp_path, ["2026-10,AAPL,120,50,1000"], name="v2.csv"))

    rows = db.query(StgEsgEmissions).filter_by(as_of_month=AS_OF, investment_id="AAPL").all()
    assert len(rows) == 1
    assert float(rows[0].scope1_tco2e) == 120
    assert rows[0].load_batch_id == result.batch_id
    assert db.query(EsgLoadBatch).count() == 2


def test_negative_emissions_rejected_with_reason(db, tmp_path):
    result = load_esg_feed(db, write_feed(tmp_path, ["2026-10,AAPL,-5,10,1000", "2026-10,MSFT,5,-10,1000"]))

    assert result.loaded_rows == 0 and result.rejected_rows == 2
    reasons = [r.reason for r in db.query(EsgLoadReject).order_by(EsgLoadReject.source_row_no)]
    assert reasons == ["scope1_tco2e must be >= 0, got -5", "scope2_tco2e must be >= 0, got -10"]


def test_missing_zero_and_non_numeric_revenue_rejected(db, tmp_path):
    result = load_esg_feed(db, write_feed(tmp_path, [
        "2026-10,AAPL,5,10,",
        "2026-10,MSFT,5,10,0",
        "2026-10,GOOGL,5,10,abc",
    ]))

    assert result.loaded_rows == 0 and result.rejected_rows == 3
    reasons = [r.reason for r in db.query(EsgLoadReject).order_by(EsgLoadReject.source_row_no)]
    assert reasons == [
        "revenue_musd missing",
        "revenue_musd must be positive, got 0",
        "revenue_musd is not numeric: 'abc'",
    ]


def test_bad_month_and_duplicate_investment_in_file_rejected(db, tmp_path):
    result = load_esg_feed(db, write_feed(tmp_path, [
        "2026-13,AAPL,5,10,100",
        "2026-10,MSFT,5,10,100",
        "2026-10,MSFT,6,10,100",
    ]))

    assert result.loaded_rows == 1 and result.rejected_rows == 2
    rejects = {r.source_row_no: r.reason for r in db.query(EsgLoadReject)}
    assert "as_of_month must be YYYY-MM" in rejects[2]
    assert rejects[4] == "duplicate investment_id MSFT for 2026-10 in file"
    assert float(db.query(StgEsgEmissions).one().scope1_tco2e) == 5


def test_missing_header_column_fails_whole_file(db, tmp_path):
    path = write_feed(tmp_path, ["2026-10,AAPL,5,10"], header="as_of_month,investment_id,scope1_tco2e,scope2_tco2e")
    with pytest.raises(EsgFeedError, match="revenue_musd"):
        load_esg_feed(db, path)
    assert db.query(EsgLoadBatch).count() == 0


def test_missing_file_raises(db, tmp_path):
    with pytest.raises(EsgFeedError, match="not found"):
        load_esg_feed(db, tmp_path / "nope.csv")


def test_corrected_resend_removes_investments_no_longer_in_file(db, tmp_path):
    load_esg_feed(db, write_feed(tmp_path, ["2026-10,AAPL,10,10,5", "2026-10,MSFT,10,10,5"], name="v1.csv"))
    assert {r.investment_id for r in db.query(StgEsgEmissions)} == {"AAPL", "MSFT"}

    result = load_esg_feed(db, write_feed(tmp_path, ["2026-10,AAPL,12,10,5", "2026-10,MSFT,10,10,"], name="v2.csv"))

    assert result.loaded_rows == 1 and result.rejected_rows == 1
    assert {r.investment_id for r in db.query(StgEsgEmissions)} == {"AAPL"}
    assert db.query(EsgLoadBatch).count() == 2
    assert db.query(EsgLoadReject).count() == 1


def test_rerun_of_mixed_month_file_reports_every_staged_month(db, tmp_path):
    feed = write_feed(tmp_path, ["2026-09,AAPL,10,10,5", "2026-10,AAPL,10,10,5"])
    first = load_esg_feed(db, feed)
    assert first.as_of_months == ["2026-09", "2026-10"]

    rerun = load_esg_feed(db, feed)
    assert rerun.skipped and rerun.as_of_months == ["2026-09", "2026-10"]
