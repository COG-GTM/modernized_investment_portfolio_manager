"""Gap hunt: feed ingestion path (RP-46, RP-52).

Adversarial tests for services.esg_service.load_esg_feed and the CLI wrapper.
Tests marked ``xfail(strict=True)`` document open findings: they fail against the
current implementation on purpose and will start failing the suite (XPASS) once
the defect is fixed, so the marker must be removed at that point.
"""
import pytest
from sqlalchemy.orm import sessionmaker

from models.esg import EsgLoadBatch, EsgLoadReject, StgEsgEmissions
from services import esg_service
from services.esg_service import EsgFeedError, compute_waci, load_esg_feed
from tests.esg.conftest import ACCOUNT, AS_OF, SAMPLE_FEED, write_feed

HEADER = "as_of_month,investment_id,scope1_tco2e,scope2_tco2e,revenue_musd"


def _write_bytes(tmp_path, name, data: bytes):
    path = tmp_path / name
    path.write_bytes(data)
    return path


def _reasons(db):
    return [r.reason for r in db.query(EsgLoadReject).order_by(EsgLoadReject.source_row_no)]


# --------------------------------------------------------------------------- encoding


@pytest.mark.parametrize("encoding", ["latin-1", "utf-16"])
def test_gap01_non_utf8_file_is_a_feed_error_not_a_traceback(db, tmp_path, encoding):
    """RP-46: a file that is not UTF-8 must fail with EsgFeedError (clean CLI exit 1), not UnicodeDecodeError,
    and must leave no batch behind."""
    path = _write_bytes(tmp_path, "esg_emissions_2026-10.csv", (HEADER + "\n2026-10,CAF\u00c9,1,2,3\n").encode(encoding))
    with pytest.raises(EsgFeedError, match="UTF-8"):
        load_esg_feed(db, path)
    assert db.query(EsgLoadBatch).count() == 0


def test_gap02_utf8_bom_and_crlf_are_accepted(db, tmp_path):
    """RP-46: a BOM-prefixed CRLF file (typical spreadsheet export) loads normally."""
    data = b"\xef\xbb\xbf" + (HEADER + "\r\n2026-10,AAPL,1,2,3\r\n").encode()
    result = load_esg_feed(db, _write_bytes(tmp_path, "esg_emissions_2026-10.csv", data))
    assert (result.loaded_rows, result.rejected_rows) == (1, 0)


def test_gap03_nul_bytes_are_rejected_as_a_file_error(db, tmp_path):
    """RP-46: a NUL byte inside a field used to be staged as part of the investment_id; the file is now refused."""
    data = (HEADER + "\n2026-10,AAPL,1,2,3\n2026-10,MS\x00FT,1,2,3\n").encode()
    with pytest.raises(EsgFeedError, match="NUL"):
        load_esg_feed(db, _write_bytes(tmp_path, "esg_emissions_2026-10.csv", data))
    assert db.query(EsgLoadBatch).count() == 0


# --------------------------------------------------------------------------- row shape


def test_gap04_blank_lines_do_not_shift_reject_row_numbers(db, tmp_path):
    """RP-46: rejects must point at the physical line of the file; a blank line used to shift source_row_no by one."""
    load_esg_feed(db, write_feed(tmp_path, ["2026-10,AAPL,1,2,3", "", "2026-10,MSFT,-1,2,3"]))
    reject = db.query(EsgLoadReject).one()
    assert reject.source_row_no == 4, "MSFT is on physical line 4 (header=1, AAPL=2, blank=3)"
    assert db.query(StgEsgEmissions).one().source_row_no == 2


def test_gap05_rows_with_extra_columns_are_rejected(db, tmp_path):
    """RP-46: a trailing comma or an extra value is a WRONG_COLUMN_COUNT reject, not a silently accepted row."""
    result = load_esg_feed(db, write_feed(tmp_path, [
        "2026-10,AAPL,1,2,3,",
        "2026-10,MSFT,1,2,3,99",
        "2026-10,GOOGL,1,2,3",
    ]))
    assert (result.loaded_rows, result.rejected_rows) == (1, 2)
    assert all("wrong column count" in r for r in _reasons(db))
    assert db.query(StgEsgEmissions).one().investment_id == "GOOGL"


def test_gap06_reordered_columns_are_accepted(db, tmp_path):
    """RP-46: the header is matched by name, so a provider re-ordering the columns still loads."""
    path = write_feed(tmp_path, ["AAPL,2026-10,3,2,1"],
                      header="investment_id,as_of_month,revenue_musd,scope2_tco2e,scope1_tco2e")
    load_esg_feed(db, path)
    row = db.query(StgEsgEmissions).one()
    assert (float(row.scope1_tco2e), float(row.scope2_tco2e), float(row.revenue_musd)) == (1, 2, 3)


def test_gap07_header_only_file_creates_an_empty_batch(db, tmp_path):
    """RP-46: a header-only file is accepted as a successful batch with zero rows (surfaced by the CLI warning, gap15)."""
    result = load_esg_feed(db, write_feed(tmp_path, []))
    assert (result.loaded_rows, result.rejected_rows, result.as_of_months) == (0, 0, [])
    assert db.query(EsgLoadBatch).one().as_of_month is None


# --------------------------------------------------------------------------- values


def test_gap08_values_outside_numeric_18_4_are_rejected(db, tmp_path):
    """RP-46 / RP-52: 1e999 used to be staged as Infinity and 20-digit values overflow Numeric(18,4);
    a revenue of 1e-999 used to be staged as 0 and silently dropped from coverage."""
    result = load_esg_feed(db, write_feed(tmp_path, [
        "2026-10,AAPL,1e999,2,3",
        "2026-10,MSFT,99999999999999999999,2,3",
        "2026-10,GOOGL,1,2,1e-999",
        "2026-10,TSLA,99999999999999.9999,2,3",
    ]))
    assert (result.loaded_rows, result.rejected_rows) == (1, 3)
    reasons = _reasons(db)
    assert "exceeds the Numeric(18,4) range" in reasons[0]
    assert "exceeds the Numeric(18,4) range" in reasons[1]
    assert "below the Numeric(18,4) precision" in reasons[2]
    assert db.query(StgEsgEmissions).one().investment_id == "TSLA"


def test_gap09_lenient_decimal_literals_are_rejected(db, tmp_path):
    """RP-46: Python's Decimal() accepts '1_000', full-width digits and 'Infinity'; the feed contract is plain decimals."""
    result = load_esg_feed(db, write_feed(tmp_path, [
        "2026-10,AAPL,1_000,2,3",
        "2026-10,MSFT,\uff11\uff12,2,3",
        "2026-10,GOOGL,Infinity,2,3",
        "2026-10,TSLA,1e3,2,3",
        "2026-10,NVDA,.5,2,3",
    ]))
    assert (result.loaded_rows, result.rejected_rows) == (2, 3)
    assert all("is not numeric" in r for r in _reasons(db))
    assert {r.investment_id for r in db.query(StgEsgEmissions)} == {"TSLA", "NVDA"}


def test_gap10_investment_id_with_control_or_whitespace_chars_is_rejected(db, tmp_path):
    """RP-46: an investment_id with an embedded tab or space can never join to positions and would silently reduce coverage."""
    result = load_esg_feed(db, write_esg_rows(tmp_path, ["2026-10,AA\tPL,1,2,3", "2026-10,MS FT,1,2,3", "2026-10,GOOGL,1,2,3"]))
    assert (result.loaded_rows, result.rejected_rows) == (1, 2)
    assert all("non-printable" in r for r in _reasons(db))


def write_esg_rows(tmp_path, rows):
    return write_feed(tmp_path, rows, name="esg_emissions_2026-10.csv")


# --------------------------------------------------------------------------- months


def test_gap11_rows_for_another_month_than_the_file_name_are_rejected(db, tmp_path):
    """RP-46: esg_emissions_2026-10.csv carrying 2026-09 rows used to overwrite September's staging rows."""
    load_esg_feed(db, write_feed(tmp_path, ["2026-09,AAPL,1,2,3"], name="esg_emissions_2026-09.csv"))
    result = load_esg_feed(db, write_feed(tmp_path, ["2026-09,AAPL,9,9,9", "2026-10,MSFT,1,2,3"],
                                          name="esg_emissions_2026-10.csv"))
    assert (result.loaded_rows, result.rejected_rows) == (1, 1)
    assert result.as_of_months == ["2026-10"]
    assert "does not match the file month 2026-10" in _reasons(db)[0]
    september = db.query(StgEsgEmissions).filter_by(as_of_month="2026-09", investment_id="AAPL").one()
    assert float(september.scope1_tco2e) == 1, "September staging must be untouched by a mis-dated October file"


def test_gap12_file_without_month_in_name_still_loads_any_valid_month(db, tmp_path):
    """RP-46: the month cross-check only applies when the file name follows esg_emissions_YYYY-MM.csv."""
    result = load_esg_feed(db, write_feed(tmp_path, ["2026-09,AAPL,1,2,3", "2026-10,MSFT,1,2,3"], name="adhoc.csv"))
    assert (result.loaded_rows, result.rejected_rows) == (2, 0)
    assert result.as_of_months == ["2026-09", "2026-10"]


# --------------------------------------------------------------------------- re-runs / atomicity


def test_gap13_same_name_different_content_is_a_new_batch_and_rerun_of_each_is_a_noop(db, tmp_path):
    """RP-46: idempotency is keyed on content (SHA-256), not the file name."""
    v1 = load_esg_feed(db, write_esg_rows(tmp_path, ["2026-10,AAPL,1,2,3"]))
    v2 = load_esg_feed(db, write_esg_rows(tmp_path, ["2026-10,AAPL,5,2,3"]))
    again = load_esg_feed(db, write_esg_rows(tmp_path, ["2026-10,AAPL,5,2,3"]))
    assert v1.batch_id != v2.batch_id
    assert again.skipped and again.batch_id == v2.batch_id
    assert db.query(EsgLoadBatch).count() == 2
    assert float(db.query(StgEsgEmissions).one().scope1_tco2e) == 5


def test_gap14_unexpected_error_mid_load_commits_nothing(db, tmp_path, monkeypatch):
    """RP-46: the batch, staging and reject rows are written in one transaction; a crash on row 3 leaves no partial batch."""
    real = esg_service.validate_feed_row
    calls = {"n": 0}

    def exploding(row, expected_month=None):
        calls["n"] += 1
        if calls["n"] == 3:
            raise RuntimeError("simulated failure mid-load")
        return real(row, expected_month)

    monkeypatch.setattr(esg_service, "validate_feed_row", exploding)
    with pytest.raises(RuntimeError):
        load_esg_feed(db, write_esg_rows(tmp_path, ["2026-10,AAPL,1,2,3", "2026-10,MSFT,-1,2,3", "2026-10,GOOGL,1,2,3"]))
    db.rollback()
    assert db.query(EsgLoadBatch).count() == 0
    assert db.query(StgEsgEmissions).count() == 0
    assert db.query(EsgLoadReject).count() == 0


def test_gap15_cli_warns_on_stderr_when_rows_are_rejected_or_nothing_staged(engine, tmp_path, monkeypatch, capsys):
    """RP-46 / RP-52: rejected rows reduce coverage_pct downstream; the CLI must surface a warning, not just exit 0."""
    from scripts import load_esg_feed as cli

    monkeypatch.setattr(cli, "SessionLocal", sessionmaker(bind=engine))
    assert cli.main([str(SAMPLE_FEED), "--no-compute"]) == 0
    err = capsys.readouterr().err
    assert "WARNING" in err and "2 row(s) rejected" in err

    assert cli.main([str(write_feed(tmp_path, [], name="esg_emissions_2026-11.csv")), "--no-compute"]) == 0
    assert "no rows were staged" in capsys.readouterr().err


# --------------------------------------------------------------------------- open findings (xfail, strict)


@pytest.mark.xfail(strict=True, reason="OPEN RP-46: corrected re-send does not retire rows the new file no longer contains")
def test_gap16_open_corrected_resend_leaves_stale_rows_from_previous_batch(db, tmp_path):
    """RP-46: after a corrected file for the same month drops MSFT, the MSFT row from batch 1 still feeds WACI."""
    load_esg_feed(db, write_esg_rows(tmp_path, ["2026-10,AAPL,1,2,3", "2026-10,MSFT,1,2,3"]))
    load_esg_feed(db, write_esg_rows(tmp_path, ["2026-10,AAPL,5,2,3"]))
    assert {r.investment_id for r in db.query(StgEsgEmissions).filter_by(as_of_month=AS_OF)} == {"AAPL"}


@pytest.mark.xfail(strict=True, reason="OPEN RP-46: a rejected correction silently keeps the superseded value in staging")
def test_gap17_open_rejected_correction_keeps_previous_value_without_warning(db, tmp_path):
    """RP-46: provider re-sends AAPL with a malformed value; the old AAPL row stays staged and nothing flags it."""
    load_esg_feed(db, write_esg_rows(tmp_path, ["2026-10,AAPL,1,2,3"]))
    result = load_esg_feed(db, write_esg_rows(tmp_path, ["2026-10,AAPL,-1,2,3"]))
    assert result.rejected_rows == 1
    staged = db.query(StgEsgEmissions).filter_by(as_of_month=AS_OF, investment_id="AAPL").first()
    assert staged is None or "superseded" in " ".join(result.rejects[0]["reason"].split()).lower()


@pytest.mark.xfail(strict=True, reason="OPEN RP-46/RP-48: rejected rows reduce coverage with no warning in the API payload")
def test_gap18_open_api_payload_does_not_surface_rejected_rows_behind_reduced_coverage(client, seeded_db):
    """RP-46 / RP-48: the sample feed rejects TSLA (missing revenue); coverage drops to ~61% and the API gives no hint why."""
    load_esg_feed(seeded_db, SAMPLE_FEED)
    compute_waci(seeded_db, AS_OF)
    body = client.get(f"/api/portfolio/{ACCOUNT}/esg").json()
    assert body["coverage_pct"] < 100
    assert any(key in body for key in ("warnings", "rejected_rows", "rejectedRows", "uncovered_holdings"))


@pytest.mark.xfail(strict=True, reason="OPEN RP-46: investment_id is case-sensitive; 'aapl' stages separately and never joins positions")
def test_gap19_open_investment_id_case_variants_stage_as_separate_rows(db, tmp_path):
    """RP-46: 'AAPL' and 'aapl' both load for the same month; only one can match positions.investment_id."""
    result = load_esg_feed(db, write_esg_rows(tmp_path, ["2026-10,AAPL,1,2,3", "2026-10,aapl,9,2,3"]))
    assert result.rejected_rows == 1
