"""RP-47 procedure tests: WACI calculation in sql/esg_waci_v1.sql via the Python wrapper."""
from datetime import date
from decimal import Decimal

import pytest

from models.esg import PortfolioEsgMetrics, StgEsgEmissions, EsgLoadBatch
from services.esg_service import compute_waci, load_esg_feed, set_override, EsgValidationError
from tests.esg.conftest import SAMPLE_FEED, AS_OF, PORT_ID, add_portfolio, add_position, write_feed


def _metric(db, port_id=PORT_ID, month=AS_OF):
    return db.query(PortfolioEsgMetrics).filter_by(portfolio_id=port_id, as_of_month=month).one()


def test_waci_matches_hand_calculation_for_sample_feed(seeded_db):
    load_esg_feed(seeded_db, SAMPLE_FEED)
    result = compute_waci(seeded_db, AS_OF)

    assert result.portfolios == 1
    metric = _metric(seeded_db)
    total_mv = 27787.50 + 37885.00 + 10692.00 + 49134.00
    expected = (
        27787.50 * (55200 + 2780) / 391035
        + 37885.00 * (144960 + 393134) / 245122
        + 10692.00 * (79400 + 2460000) / 350018
    ) / total_mv
    assert float(metric.waci_computed) == pytest.approx(expected, rel=1e-6)
    # TSLA (missing revenue, rejected by the loader) counts against coverage
    assert float(metric.coverage_pct) == pytest.approx((27787.50 + 37885.00 + 10692.00) / total_mv * 100, abs=1e-3)
    assert float(metric.total_market_value) == pytest.approx(total_mv)
    assert float(metric.covered_market_value) == pytest.approx(27787.50 + 37885.00 + 10692.00)
    assert metric.computed_at is not None
    assert metric.override_value is None


def test_holding_with_null_revenue_in_staging_is_excluded_and_reduces_coverage(db, tmp_path):
    add_portfolio(db)
    add_position(db, "AAA", "600")
    add_position(db, "BBB", "400")
    load_esg_feed(db, write_feed(tmp_path, ["2026-10,AAA,100,0,10"]))
    db.add(EsgLoadBatch(batch_id="manual", file_name="manual", file_sha256="x" * 64, loaded_at=date.today(), loaded_rows=1, rejected_rows=0))
    db.add(StgEsgEmissions(load_batch_id="manual", as_of_month=AS_OF, investment_id="BBB",
                           scope1_tco2e=Decimal("50"), scope2_tco2e=Decimal("50"), revenue_musd=None, loaded_at=date.today()))
    db.commit()

    compute_waci(db, AS_OF)

    metric = _metric(db)
    # only AAA contributes: weight 0.6 * (100/10)
    assert float(metric.waci_computed) == pytest.approx(0.6 * 10)
    assert float(metric.coverage_pct) == pytest.approx(60.0)


def test_zero_total_market_value_does_not_divide_by_zero(db, tmp_path):
    add_portfolio(db)
    add_position(db, "AAA", "0")
    load_esg_feed(db, write_feed(tmp_path, ["2026-10,AAA,100,0,10"]))

    compute_waci(db, AS_OF)

    metric = _metric(db)
    assert metric.waci_computed is None
    assert float(metric.coverage_pct) == 0
    assert float(metric.total_market_value) == 0


def test_portfolio_without_positions_gets_empty_metric(db):
    add_portfolio(db)
    db.commit()
    compute_waci(db, AS_OF)
    metric = _metric(db)
    assert metric.waci_computed is None and float(metric.coverage_pct) == 0


def test_position_sold_mid_month_is_excluded(db, tmp_path):
    add_portfolio(db)
    add_position(db, "AAA", "500")
    add_position(db, "SOLD", "500", status="C", on=date(2026, 10, 15))
    load_esg_feed(db, write_feed(tmp_path, ["2026-10,AAA,100,0,10", "2026-10,SOLD,9000,0,10"]))

    compute_waci(db, AS_OF)

    metric = _metric(db)
    assert float(metric.waci_computed) == pytest.approx(10.0)
    assert float(metric.coverage_pct) == pytest.approx(100.0)
    assert float(metric.total_market_value) == pytest.approx(500)


def test_holding_without_feed_row_counts_against_coverage(db, tmp_path):
    add_portfolio(db)
    add_position(db, "AAA", "750")
    add_position(db, "NOFEED", "250")
    load_esg_feed(db, write_feed(tmp_path, ["2026-10,AAA,20,20,4"]))

    compute_waci(db, AS_OF)

    metric = _metric(db)
    assert float(metric.waci_computed) == pytest.approx(0.75 * 10)
    assert float(metric.coverage_pct) == pytest.approx(75.0)


def test_rerun_is_idempotent_and_preserves_override(seeded_db):
    load_esg_feed(seeded_db, SAMPLE_FEED)
    compute_waci(seeded_db, AS_OF)
    first = _metric(seeded_db)
    first_value = float(first.waci_computed)
    set_override(seeded_db, PORT_ID, Decimal("2.5"), "Provider restated scope 2 figures", "pm_user")

    compute_waci(seeded_db, AS_OF)

    rows = seeded_db.query(PortfolioEsgMetrics).filter_by(as_of_month=AS_OF).all()
    assert len(rows) == 1
    assert float(rows[0].waci_computed) == pytest.approx(first_value)
    assert float(rows[0].override_value) == 2.5
    assert rows[0].override_reason == "Provider restated scope 2 figures"


def test_only_matching_month_is_used(db, tmp_path):
    add_portfolio(db)
    add_position(db, "AAA", "100", on=date(2026, 9, 30))
    add_position(db, "AAA", "100")
    load_esg_feed(db, write_feed(tmp_path, ["2026-09,AAA,100,0,10"], name="sep.csv"))
    load_esg_feed(db, write_feed(tmp_path, ["2026-10,AAA,200,0,10"], name="oct.csv"))

    compute_waci(db, "2026-09")
    compute_waci(db, "2026-10")

    assert float(_metric(db, month="2026-09").waci_computed) == pytest.approx(10.0)
    assert float(_metric(db, month="2026-10").waci_computed) == pytest.approx(20.0)


def test_invalid_month_rejected():
    with pytest.raises(EsgValidationError):
        compute_waci(None, "October")


def test_alembic_migration_creates_esg_tables(tmp_path):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect
    from tests.esg.conftest import BACKEND_DIR

    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    tables = set(inspect(create_engine(url)).get_table_names())
    assert {"esg_load_batches", "stg_esg_emissions", "esg_load_rejects", "portfolio_esg_metrics", "esg_override_audit"} <= tables
