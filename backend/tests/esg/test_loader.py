"""SSTCNTRL-2: ingest the monthly ESG feed from the inbound bucket into staging."""
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from esg import load_esg_feed as cli
from esg import loader
from esg.loader import EsgFeedError, load_all, load_feed
from models.esg import EsgLoadBatch, EsgLoadReject, StgEsgEmission

BACKEND = Path(__file__).resolve().parents[2]
SAMPLE_FEED = BACKEND / "inbound" / "esg" / "2026-10" / "esg_emissions_2026-10.csv"
HEADER = "as_of_month,investment_id,scope1_tco2e,scope2_tco2e,revenue_musd"


def write_feed(root: Path, month: str, rows, header: str = HEADER, raw: bytes | None = None) -> Path:
    path = root / "esg" / month / f"esg_emissions_{month}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        path.write_bytes(raw)
    else:
        path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    return path


def counts(session):
    return (
        session.query(EsgLoadBatch).count(),
        session.query(StgEsgEmission).count(),
        session.query(EsgLoadReject).count(),
    )


def staged(session, month="2026-10"):
    return {r.investment_id: r for r in session.query(StgEsgEmission).filter_by(as_of_month=month)}


def reasons(session, batch_id=None):
    query = session.query(EsgLoadReject)
    if batch_id is not None:
        query = query.filter_by(batch_id=batch_id)
    return [r.reason for r in query.order_by(EsgLoadReject.reject_id)]


@pytest.fixture
def inbound(tmp_path, monkeypatch):
    root = tmp_path / "inbound"
    monkeypatch.setenv(loader.INBOUND_ROOT_ENV, str(root))
    return root


class TestSampleFile:
    def test_sample_file_yields_expected_counts(self, session):
        result = load_feed(session, SAMPLE_FEED, BACKEND / "inbound")

        assert (result.status, result.row_count, result.accepted_count, result.rejected_count) == ("C", 5, 4, 1)
        batch = session.get(EsgLoadBatch, result.batch_id)
        assert batch.file_path == "esg/2026-10/esg_emissions_2026-10.csv"
        assert batch.as_of_month == "2026-10"
        assert len(batch.file_sha256) == 64
        assert (batch.row_count, batch.accepted_count, batch.rejected_count, batch.failure_reason) == (5, 4, 1, None)

        rows = staged(session)
        assert set(rows) == {"AAPL", "MSFT", "GOOGL", "TSLA"}
        assert {r.batch_id for r in rows.values()} == {result.batch_id}
        assert (rows["AAPL"].scope1_tco2e, rows["AAPL"].scope2_tco2e, rows["AAPL"].revenue_musd) == (
            Decimal(10), Decimal(40), Decimal("2.5"),
        )
        assert rows["GOOGL"].revenue_musd is None, "empty revenue is staged as NULL, not 0"
        assert rows["TSLA"].source_row_no == 4

        reject = session.query(EsgLoadReject).one()
        assert reject.batch_id == result.batch_id
        assert reject.source_row_no == 5
        assert reject.raw_line == "2026-10,NVDA,5,-3,4.0"
        assert reject.reason.startswith("INVALID_SCOPE2:")

    def test_second_run_is_a_noop(self, session):
        first = load_feed(session, SAMPLE_FEED, BACKEND / "inbound")
        before = counts(session)
        second = load_feed(session, SAMPLE_FEED, BACKEND / "inbound")

        assert second.skipped and second.batch_id == first.batch_id and second.exit_code == 0
        assert counts(session) == before == (1, 4, 1)


class TestRowRejects:
    def test_reason_codes(self, session, inbound):
        path = write_feed(inbound, "2026-10", [
            "2026-10,OK1,1,2,3",
            "2026-13,BADMONTH,1,2,3",
            "2026-09,OTHERMONTH,1,2,3",
            "2026-10,,1,2,3",
            "2026-10,ELEVENCHARS,1,2,3",
            "2026-10,NEG1,-1,2,3",
            "2026-10,TEXT1,abc,2,3",
            "2026-10,NEG2,1,-0.5,3",
            "2026-10,ZEROREV,1,2,0",
            "2026-10,NEGREV,1,2,-4",
            "2026-10,TEXTREV,1,2,n/a",
            "2026-10,OK1,9,9,9",
            "2026-10,SHORT,1,2",
            "2026-10,LONG,1,2,3,4",
            "2026-10,OK2,0,0,",
        ])
        result = load_feed(session, path)

        assert (result.status, result.row_count, result.accepted_count, result.rejected_count) == ("C", 15, 2, 13)
        assert [r.split(":")[0] for r in reasons(session)] == [
            "INVALID_AS_OF_MONTH",
            "INVALID_AS_OF_MONTH",
            "MISSING_INVESTMENT_ID",
            "MISSING_INVESTMENT_ID",
            "INVALID_SCOPE1",
            "INVALID_SCOPE1",
            "INVALID_SCOPE2",
            "INVALID_REVENUE",
            "INVALID_REVENUE",
            "INVALID_REVENUE",
            "DUPLICATE_INVESTMENT_ID",
            "WRONG_COLUMN_COUNT",
            "WRONG_COLUMN_COUNT",
        ]
        rows = staged(session)
        assert set(rows) == {"OK1", "OK2"}
        assert rows["OK1"].scope1_tco2e == Decimal(1), "the first occurrence of a duplicate id is kept"
        assert session.query(StgEsgEmission).filter_by(as_of_month="2026-09").count() == 0

    def test_negative_emissions_reason_names_the_problem(self, session, inbound):
        load_feed(session, write_feed(inbound, "2026-10", ["2026-10,A,1,2,3", "2026-10,B,-1,2,3"]))
        assert "non-negative" in reasons(session)[0]

    @pytest.mark.parametrize("value", ["NaN", "Infinity", "1_000", "\uff11\uff12", "1,5", "0x10"])
    def test_non_plain_numbers_are_rejected(self, session, inbound, value):
        line = f'2026-10,B,"{value}",2,3'
        load_feed(session, write_feed(inbound, "2026-10", ["2026-10,A,1,2,3", line]))
        assert reasons(session)[0].startswith("INVALID_SCOPE1:")

    def test_values_outside_numeric_18_4_are_rejected(self, session, inbound):
        load_feed(session, write_feed(inbound, "2026-10", [
            "2026-10,A,1e999,2,3",
            "2026-10,B,99999999999999.99995,2,3",
            "2026-10,C,1,2,0.00004",
            "2026-10,D,1e3,2,.5",
            "2026-10,E,1,2,0.00009",
        ]))
        assert [r.split(":")[0] for r in reasons(session)] == ["INVALID_SCOPE1", "INVALID_SCOPE1", "INVALID_REVENUE"]
        rows = staged(session)
        assert rows["D"].scope1_tco2e == Decimal(1000) and rows["D"].revenue_musd == Decimal("0.5")
        assert rows["E"].revenue_musd == Decimal("0.0001")

    def test_investment_id_with_whitespace_is_rejected(self, session, inbound):
        load_feed(session, write_feed(inbound, "2026-10", ["2026-10,AA\tPL,1,2,3", "2026-10,MS FT,1,2,3", "2026-10,OK,1,2,3"]))
        assert [r.split(":")[0] for r in reasons(session)] == ["MISSING_INVESTMENT_ID"] * 2

    def test_bom_crlf_and_blank_lines(self, session, inbound):
        raw = b"\xef\xbb\xbf" + f"{HEADER}\r\n2026-10,A,1,2,3\r\n  \r\n2026-10,B,-1,2,3\r\n".encode()
        result = load_feed(session, write_feed(inbound, "2026-10", [], raw=raw))
        assert (result.row_count, result.accepted_count, result.rejected_count) == (2, 1, 1)
        assert session.query(EsgLoadReject).one().source_row_no == 3, "row numbers follow the file's physical lines"


class TestFileLevel:
    def test_bad_header_fails_the_batch_and_leaves_staging(self, session, inbound):
        load_feed(session, write_feed(inbound, "2026-10", ["2026-10,A,1,2,3"]))
        result = load_feed(session, write_feed(inbound, "2026-10", ["A,2026-10,1,2,3"],
                                               header="investment_id,as_of_month,scope1_tco2e,scope2_tco2e,revenue_musd"))
        assert (result.status, result.failure_reason, result.exit_code) == ("F", "BAD_HEADER", 1)
        assert set(staged(session)) == {"A"}

    def test_header_only_file_fails_with_empty_file(self, session, inbound):
        load_feed(session, write_feed(inbound, "2026-10", ["2026-10,A,1,2,3"]))
        result = load_feed(session, write_feed(inbound, "2026-10", []))
        assert (result.status, result.failure_reason, result.row_count) == ("F", "EMPTY_FILE", 0)
        assert set(staged(session)) == {"A"}

    def test_all_rows_rejected_fails_writes_rejects_and_leaves_staging(self, session, inbound):
        load_feed(session, write_feed(inbound, "2026-10", ["2026-10,A,1,2,3"]))
        result = load_feed(session, write_feed(inbound, "2026-10", ["2026-10,A,-1,2,3", "2026-10,B,x,2,3"]))
        assert (result.status, result.failure_reason, result.rejected_count, result.accepted_count) == ("F", "ALL_ROWS_REJECTED", 2, 0)
        assert len(reasons(session, result.batch_id)) == 2
        assert staged(session)["A"].scope1_tco2e == Decimal(1)

    def test_rerunning_a_failed_file_does_not_duplicate_rejects(self, session, inbound):
        path = write_feed(inbound, "2026-10", ["2026-10,A,-1,2,3"])
        first = load_feed(session, path)
        again = load_feed(session, path)
        assert again.skipped and again.batch_id == first.batch_id and again.exit_code == 1
        assert counts(session) == (1, 0, 1)

    @pytest.mark.parametrize("raw", [f"{HEADER}\n2026-10,CAF\u00c9,1,2,3\n".encode("latin-1"), f"{HEADER}\n2026-10,A\x00,1,2,3\n".encode()])
    def test_unreadable_file_writes_no_batch(self, session, inbound, raw):
        with pytest.raises(EsgFeedError):
            load_feed(session, write_feed(inbound, "2026-10", [], raw=raw))
        assert counts(session) == (0, 0, 0)

    def test_misnamed_or_misplaced_file_is_refused(self, session, tmp_path):
        bad_name = tmp_path / "esg" / "2026-10" / "emissions.csv"
        bad_name.parent.mkdir(parents=True)
        bad_name.write_text(HEADER + "\n2026-10,A,1,2,3\n")
        wrong_folder = tmp_path / "esg" / "2026-09" / "esg_emissions_2026-10.csv"
        wrong_folder.parent.mkdir(parents=True)
        wrong_folder.write_text(HEADER + "\n2026-10,A,1,2,3\n")
        for path in (bad_name, wrong_folder):
            with pytest.raises(EsgFeedError):
                load_feed(session, path)
        assert counts(session) == (0, 0, 0)

    def test_missing_file_raises(self, session, inbound):
        with pytest.raises(FileNotFoundError):
            load_feed(session, inbound / "esg" / "2026-10" / "esg_emissions_2026-10.csv")

    def test_unexpected_error_mid_load_commits_nothing(self, session, inbound, monkeypatch):
        def boom(*_args, **_kwargs):
            raise RuntimeError("simulated failure")

        monkeypatch.setattr(loader, "_upsert_staging", boom)
        with pytest.raises(RuntimeError):
            load_feed(session, write_feed(inbound, "2026-10", ["2026-10,A,1,2,3", "2026-10,B,-1,2,3"]))
        assert counts(session) == (0, 0, 0)


class TestCorrections:
    def test_corrected_file_replaces_the_month_snapshot(self, session, inbound):
        first = load_feed(session, write_feed(inbound, "2026-10", ["2026-10,A,1,2,3", "2026-10,B,1,2,3", "2026-10,C,-1,2,3"]))
        second = load_feed(session, write_feed(inbound, "2026-10", ["2026-10,A,5,2,3"]))

        assert second.batch_id != first.batch_id and not second.skipped
        rows = staged(session)
        assert set(rows) == {"A"}, "B was dropped by the corrected file"
        assert rows["A"].scope1_tco2e == Decimal(5) and rows["A"].batch_id == second.batch_id
        assert session.query(EsgLoadBatch).count() == 2, "earlier batch is retained"
        assert len(reasons(session, first.batch_id)) == 1, "earlier rejects are retained"

    def test_replaying_the_original_after_a_correction_restores_it_as_a_new_batch(self, session, inbound):
        original = ["2026-10,A,1,2,3", "2026-10,B,1,2,3"]
        load_feed(session, write_feed(inbound, "2026-10", original))
        load_feed(session, write_feed(inbound, "2026-10", ["2026-10,A,5,2,3"]))
        third = load_feed(session, write_feed(inbound, "2026-10", original))

        assert not third.skipped and third.batch_id == 3
        assert set(staged(session)) == {"A", "B"}
        assert staged(session)["A"].scope1_tco2e == Decimal(1)

    def test_loading_one_month_never_touches_another(self, session, inbound):
        load_feed(session, write_feed(inbound, "2026-09", ["2026-09,A,1,2,3", "2026-09,B,1,2,3"]))
        load_feed(session, write_feed(inbound, "2026-10", ["2026-10,A,5,2,3", "2026-09,B,9,9,9"]))
        assert {k: r.scope1_tco2e for k, r in staged(session, "2026-09").items()} == {"A": Decimal(1), "B": Decimal(1)}
        assert set(staged(session, "2026-10")) == {"A"}


class TestAllAndCli:
    def test_all_loads_every_file_not_yet_loaded(self, session, inbound):
        write_feed(inbound, "2026-09", ["2026-09,A,1,2,3"])
        write_feed(inbound, "2026-10", ["2026-10,A,1,2,3", "2026-10,B,1,2,3"])
        first = load_all(session)
        assert [(r.as_of_month, r.skipped) for r in first] == [("2026-09", False), ("2026-10", False)]

        write_feed(inbound, "2026-11", ["2026-11,A,1,2,3"])
        second = load_all(session)
        assert [(r.as_of_month, r.skipped) for r in second] == [("2026-09", True), ("2026-10", True), ("2026-11", False)]
        assert counts(session) == (3, 4, 0)

    def test_cli_file_rerun_and_failure_exit_codes(self, session_factory, session, inbound, monkeypatch, capsys):
        monkeypatch.setattr(cli, "SessionLocal", session_factory)
        path = write_feed(inbound, "2026-10", ["2026-10,A,1,2,3", "2026-10,B,-1,2,3"])

        assert cli.main(["--file", str(path)]) == 0
        out = capsys.readouterr()
        assert "batch 1 status C, 2 rows, 1 accepted, 1 rejected" in out.out
        assert "WARNING" in out.err and "1 row(s) rejected" in out.err

        assert cli.main(["--file", str(path)]) == 0
        assert "already loaded as batch 1" in capsys.readouterr().out
        assert counts(session) == (1, 1, 1)

        bad = write_feed(inbound, "2026-11", [])
        assert cli.main(["--file", str(bad)]) == 1
        assert "EMPTY_FILE" in capsys.readouterr().err

        assert cli.main(["--file", str(inbound / "esg" / "2026-12" / "esg_emissions_2026-12.csv")]) == 1

    def test_cli_all(self, session_factory, session, inbound, monkeypatch):
        monkeypatch.setattr(cli, "SessionLocal", session_factory)
        write_feed(inbound, "2026-10", ["2026-10,A,1,2,3"])
        assert cli.main(["--all", "--inbound-root", str(inbound)]) == 0
        assert cli.main(["--all", "--inbound-root", str(inbound)]) == 0
        assert counts(session) == (1, 1, 0)


def test_migration_creates_and_drops_the_load_tables(tmp_path, monkeypatch):
    monkeypatch.chdir(BACKEND)
    db_url = f"sqlite:///{tmp_path / 'migrated.db'}"
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", db_url)
    tables = {"esg_load_batches", "stg_esg_emissions", "esg_load_rejects"}

    command.upgrade(config, "head")
    engine = create_engine(db_url)
    inspector = inspect(engine)
    assert tables <= set(inspector.get_table_names())
    assert inspector.get_pk_constraint("stg_esg_emissions")["constrained_columns"] == ["as_of_month", "investment_id"]

    command.downgrade(config, "40a256798f94")
    assert not tables & set(inspect(engine).get_table_names())
    engine.dispose()


class TestReviewFollowUps:
    def test_quoted_cell_spanning_lines_is_one_record(self, session, inbound):
        raw = f'{HEADER}\n2026-10,A,1,2,3\n2026-10,"BAD\n2026-10,FAKE,1,2,3",1,2,3\n2026-10,B,1,2,3\n'.encode()
        result = load_feed(session, write_feed(inbound, "2026-10", [], raw=raw))

        assert (result.row_count, result.accepted_count, result.rejected_count) == (3, 2, 1)
        assert set(staged(session)) == {"A", "B"}
        reject = session.query(EsgLoadReject).one()
        assert reject.reason.startswith("MISSING_INVESTMENT_ID:")
        assert reject.source_row_no == 2
        assert reject.raw_line == '2026-10,"BAD\n2026-10,FAKE,1,2,3",1,2,3'
        assert staged(session)["B"].source_row_no == 4, "row numbers still follow physical lines"

    def test_rejected_multiline_record_keeps_its_line_endings(self, session, inbound):
        raw = f'{HEADER}\r\n2026-10,A,1,2,3\r\n2026-10,"B\r\nC",1,2,3\r\n2026-10,D,-1,2,3\r\n'.encode()
        load_feed(session, write_feed(inbound, "2026-10", [], raw=raw))
        assert [r.raw_line for r in session.query(EsgLoadReject).order_by(EsgLoadReject.reject_id)] == [
            '2026-10,"B\r\nC",1,2,3',
            "2026-10,D,-1,2,3",
        ]

    def test_feed_larger_than_sqlite_bind_limit_loads(self, session, inbound):
        rows = [f"2026-10,ID{i:05d},1.5,2.5,3.5" for i in range(6000)]
        result = load_feed(session, write_feed(inbound, "2026-10", rows))
        assert (result.status, result.accepted_count) == ("C", 6000)
        assert session.query(StgEsgEmission).count() == 6000

    @staticmethod
    def _race(tmp_path, first_path, second_path):
        """Start a second load of the month while the first is mid-transaction; return the db session factory."""
        import threading

        from sqlalchemy.orm import sessionmaker

        from models.database import Base

        engine = create_engine(f"sqlite:///{tmp_path / 'race.db'}", connect_args={"timeout": 30})
        Base.metadata.create_all(engine)
        factory = sessionmaker(bind=engine)
        in_upsert, release = threading.Event(), threading.Event()
        original = loader._upsert_staging
        errors, results = [], []

        def slow_upsert(session, rows):
            original(session, rows)
            if not in_upsert.is_set():
                in_upsert.set()
                release.wait(5)

        def run(path):
            session = factory()
            try:
                results.append(load_feed(session, path, path.parents[2]))
            except Exception as exc:  # noqa: BLE001  surfaced by the assertion below
                errors.append(exc)
            finally:
                session.close()

        loader._upsert_staging = slow_upsert
        try:
            t1 = threading.Thread(target=run, args=(first_path,))
            t1.start()
            assert in_upsert.wait(5)
            t2 = threading.Thread(target=run, args=(second_path,))
            t2.start()
            t2.join(0.5)
            release.set()
            t1.join(10)
            t2.join(10)
        finally:
            loader._upsert_staging = original
        assert not errors
        return factory, results

    def test_concurrent_loads_of_one_month_do_not_merge_snapshots(self, tmp_path, inbound):
        first = write_feed(inbound / "a", "2026-10", ["2026-10,AAPL,1,2,3"])
        second = write_feed(inbound / "b", "2026-10", ["2026-10,MSFT,1,2,3"])
        factory, _ = self._race(tmp_path, first, second)
        session = factory()
        assert set(staged(session)) == {"MSFT"}, "the later load replaces the earlier snapshot"
        assert session.query(EsgLoadBatch).count() == 2
        session.close()

    def test_concurrent_runs_of_the_same_file_load_it_once(self, tmp_path, inbound):
        path = write_feed(inbound / "a", "2026-10", ["2026-10,AAPL,1,2,3", "2026-10,MSFT,-1,2,3"])
        factory, results = self._race(tmp_path, path, path)
        session = factory()
        assert sorted(r.skipped for r in results) == [False, True]
        assert counts(session) == (1, 1, 1)
        session.close()

    def test_skipped_rerun_keeps_the_callers_pending_changes(self, session, inbound):
        path = write_feed(inbound, "2026-10", ["2026-10,A,1,2,3"])
        load_feed(session, path)
        session.add(EsgLoadBatch(file_path="x", file_sha256="0" * 64, as_of_month="2026-09", loaded_at=datetime.now(),
                                 row_count=0, accepted_count=0, rejected_count=0, status="F", failure_reason="EMPTY_FILE"))
        assert load_feed(session, path).skipped
        session.rollback()
        assert session.query(EsgLoadBatch).filter_by(as_of_month="2026-09").count() == 1
