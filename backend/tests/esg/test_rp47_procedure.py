"""RP-47: Compute WACI per portfolio in a database procedure."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from tests.esg.conftest import (
    AS_OF_MONTH,
    BACKEND_DIR,
    EXPECTED_COVERAGE_MAIN,
    EXPECTED_COVERAGE_MAIN_2026_11,
    EXPECTED_WACI_MAIN,
    EXPECTED_WACI_MAIN_2026_11,
    MAIN_FEED_ROWS_2026_10,
    METRICS_TABLE,
    NEXT_MONTH,
    PORTFOLIO_MAIN,
    PORTFOLIO_NO_METRIC,
    PORTFOLIO_ZERO_MV,
    EsgDb,
    add_position,
    approx_equal,
    as_decimal,
    field,
    stage_emissions,
)

esg_service = pytest.importorskip(
    "services.esg_service",
    reason="RP-47: backend/services/esg_service.py is not implemented yet",
)

pytestmark = [pytest.mark.esg, pytest.mark.rp47]

SQL_DIR = BACKEND_DIR / "sql"


def _metric_row(db: EsgDb, portfolio_id: str, month: str = AS_OF_MONTH):
    rows = db.rows(
        f"SELECT * FROM {METRICS_TABLE} WHERE portfolio_id = :p AND as_of_month = :m",
        p=portfolio_id,
        m=month,
    )
    assert len(rows) <= 1, "metrics must be keyed by (portfolio, as_of_month)"
    return rows[0] if rows else None


def _value(row) -> Decimal | None:
    return as_decimal(field(row, "computed_value", "waci", "value"))


def _metric_for(metrics, portfolio_id: str):
    for m in metrics:
        if field(m, "portfolio_id", "port_id") == portfolio_id:
            return m
    return None


def test_rp47_01_calculation_lives_in_a_versioned_sql_script():
    """RP-47 AC: the calculation is kept in SQL as a versioned script under backend/sql/."""
    assert SQL_DIR.is_dir(), "backend/sql/ must exist"
    scripts = sorted(p for p in SQL_DIR.glob("*.sql") if "waci" in p.name.lower() or "esg" in p.name.lower())
    assert scripts, "expected a versioned WACI script such as backend/sql/V001__compute_portfolio_waci.sql"
    body = scripts[-1].read_text().lower()
    assert "insert" in body or "replace" in body
    assert "portfolio_esg_metrics" in body
    assert "market_value" in body
    assert "revenue_musd" in body


def test_rp47_02_sql_script_handles_insert_or_replace_for_idempotency():
    """RP-47 AC: the SQL itself upserts on (portfolio, as_of_month) so reruns stay idempotent."""
    scripts = sorted(SQL_DIR.glob("*.sql")) if SQL_DIR.is_dir() else []
    assert scripts, "no SQL scripts under backend/sql/"
    body = " ".join(p.read_text().lower() for p in scripts)
    assert any(token in body for token in ("insert or replace", "on conflict", "delete from portfolio_esg_metrics", "merge"))


def test_rp47_03_waci_matches_hand_computed_value(seeded_portfolios: EsgDb):
    """RP-47 AC: WACI = sum(weight_i * (scope1+scope2)_i / revenue_i), weight = market value share. Expected 3.3."""
    db = seeded_portfolios
    stage_emissions(db, MAIN_FEED_ROWS_2026_10)

    metrics = esg_service.compute_waci(AS_OF_MONTH)

    main = _metric_for(metrics, PORTFOLIO_MAIN)
    assert main is not None, "compute_waci must return a metric for PORT0001"
    assert approx_equal(_value(main), EXPECTED_WACI_MAIN), f"expected WACI 3.3, got {_value(main)}"

    row = _metric_row(db, PORTFOLIO_MAIN)
    assert row is not None, "metric must be persisted in portfolio_esg_metrics"
    assert approx_equal(_value(row), EXPECTED_WACI_MAIN)


def test_rp47_04_metric_row_has_required_columns(seeded_portfolios: EsgDb):
    """RP-47 AC: results keyed by (portfolio, as_of_month) with computed_at and coverage_pct."""
    db = seeded_portfolios
    stage_emissions(db, MAIN_FEED_ROWS_2026_10)
    esg_service.compute_waci(AS_OF_MONTH)

    cols = set(db.columns(METRICS_TABLE))
    assert {"portfolio_id", "as_of_month", "computed_at", "coverage_pct"} <= cols
    row = _metric_row(db, PORTFOLIO_MAIN)
    assert row["as_of_month"] == AS_OF_MONTH
    assert row["computed_at"] is not None


def test_rp47_05_missing_revenue_is_excluded_and_counts_against_coverage(seeded_portfolios: EsgDb):
    """RP-47 AC: holdings with missing revenue are excluded and counted against coverage (90 %)."""
    db = seeded_portfolios
    stage_emissions(db, MAIN_FEED_ROWS_2026_10)
    metrics = esg_service.compute_waci(AS_OF_MONTH)

    main = _metric_for(metrics, PORTFOLIO_MAIN)
    coverage = as_decimal(field(main, "coverage_pct"))
    assert approx_equal(coverage, EXPECTED_COVERAGE_MAIN, Decimal("0.05")), f"coverage expected 90.0, got {coverage}"
    assert approx_equal(_value(main), EXPECTED_WACI_MAIN)


def test_rp47_06_holding_absent_from_feed_counts_against_coverage(seeded_portfolios: EsgDb):
    """RP-47 AC (edge): a holding with no feed row at all is treated like missing data, not zero emissions."""
    db = seeded_portfolios
    rows = [r for r in MAIN_FEED_ROWS_2026_10 if r["investment_id"] != "INV0000003"]
    stage_emissions(db, rows)
    metrics = esg_service.compute_waci(AS_OF_MONTH)

    main = _metric_for(metrics, PORTFOLIO_MAIN)
    assert approx_equal(as_decimal(field(main, "coverage_pct")), EXPECTED_COVERAGE_MAIN, Decimal("0.05"))
    assert approx_equal(_value(main), EXPECTED_WACI_MAIN)


def test_rp47_07_full_coverage_when_every_holding_has_revenue(seeded_portfolios: EsgDb):
    """RP-47 AC: with revenue for every holding coverage is 100 % (2026-11 fixture, WACI 3.075)."""
    db = seeded_portfolios
    session = db.Session()
    try:
        add_position(session, PORTFOLIO_MAIN, "INV0000001", "60000.00", on=date(2026, 11, 30))
        add_position(session, PORTFOLIO_MAIN, "INV0000002", "30000.00", on=date(2026, 11, 30))
        add_position(session, PORTFOLIO_MAIN, "INV0000003", "10000.00", on=date(2026, 11, 30))
        session.commit()
    finally:
        session.close()
    stage_emissions(
        db,
        [
            {"investment_id": "INV0000001", "scope1_tco2e": 100.0, "scope2_tco2e": 100.0, "revenue_musd": 50.0},
            {"investment_id": "INV0000002", "scope1_tco2e": 20.0, "scope2_tco2e": 10.0, "revenue_musd": 15.0},
            {"investment_id": "INV0000003", "scope1_tco2e": 10.0, "scope2_tco2e": 5.0, "revenue_musd": 20.0},
        ],
        as_of_month=NEXT_MONTH,
        batch_id="batch-test-0002",
    )
    metrics = esg_service.compute_waci(NEXT_MONTH)
    main = _metric_for(metrics, PORTFOLIO_MAIN)
    assert approx_equal(_value(main), EXPECTED_WACI_MAIN_2026_11)
    assert approx_equal(as_decimal(field(main, "coverage_pct")), EXPECTED_COVERAGE_MAIN_2026_11, Decimal("0.05"))


def test_rp47_08_zero_total_market_value_does_not_divide_by_zero(seeded_portfolios: EsgDb):
    """RP-47 AC: zero total market value must not divide by zero."""
    db = seeded_portfolios
    stage_emissions(db, MAIN_FEED_ROWS_2026_10)

    metrics = esg_service.compute_waci(AS_OF_MONTH)  # must not raise

    zero = _metric_for(metrics, PORTFOLIO_ZERO_MV)
    row = _metric_row(db, PORTFOLIO_ZERO_MV)
    if zero is None and row is None:
        pytest.fail("PORT0002 (zero market value) produced no metric row; expected NULL/0 value with 0 coverage")
    value = _value(zero if zero is not None else row)
    assert value is None or value == 0
    coverage = as_decimal(field(zero if zero is not None else row, "coverage_pct"))
    assert coverage is None or coverage == 0


def test_rp47_09_position_sold_mid_month_is_excluded(seeded_portfolios: EsgDb):
    """RP-52 AC: a position sold mid-month (status C) is not an active position and does not move WACI."""
    db = seeded_portfolios
    session = db.Session()
    try:
        add_position(session, PORTFOLIO_MAIN, "INV0000004", "40000.00", on=date(2026, 10, 15), status="C")
        session.commit()
    finally:
        session.close()
    stage_emissions(db, MAIN_FEED_ROWS_2026_10)

    metrics = esg_service.compute_waci(AS_OF_MONTH)
    main = _metric_for(metrics, PORTFOLIO_MAIN)
    assert approx_equal(_value(main), EXPECTED_WACI_MAIN), (
        f"closed position leaked into WACI: got {_value(main)}, expected 3.3 (10.93 if wrongly included)"
    )
    assert approx_equal(as_decimal(field(main, "coverage_pct")), EXPECTED_COVERAGE_MAIN, Decimal("0.05"))


def test_rp47_10_positions_from_other_months_are_ignored(seeded_portfolios: EsgDb):
    """RP-47 AC: only positions for the as-of month are used."""
    db = seeded_portfolios
    session = db.Session()
    try:
        add_position(session, PORTFOLIO_MAIN, "INV0000004", "40000.00", on=date(2026, 9, 30))
        session.commit()
    finally:
        session.close()
    stage_emissions(db, MAIN_FEED_ROWS_2026_10)

    metrics = esg_service.compute_waci(AS_OF_MONTH)
    assert approx_equal(_value(_metric_for(metrics, PORTFOLIO_MAIN)), EXPECTED_WACI_MAIN)


def test_rp47_11_rerun_is_idempotent(seeded_portfolios: EsgDb):
    """RP-47 AC: rerun is idempotent - one row per (portfolio, as_of_month), same value, newer computed_at."""
    db = seeded_portfolios
    stage_emissions(db, MAIN_FEED_ROWS_2026_10)
    esg_service.compute_waci(AS_OF_MONTH)
    first = _metric_row(db, PORTFOLIO_MAIN)
    esg_service.compute_waci(AS_OF_MONTH)
    second = _metric_row(db, PORTFOLIO_MAIN)

    assert db.count(METRICS_TABLE, "portfolio_id = :p AND as_of_month = :m", p=PORTFOLIO_MAIN, m=AS_OF_MONTH) == 1
    assert _value(first) == _value(second)
    assert str(second["computed_at"]) >= str(first["computed_at"])


def test_rp47_12_rerun_picks_up_restated_emissions(seeded_portfolios: EsgDb):
    """RP-47 AC (edge): a rerun after the staging data changed replaces the stored value rather than keeping the old one."""
    db = seeded_portfolios
    stage_emissions(db, MAIN_FEED_ROWS_2026_10)
    esg_service.compute_waci(AS_OF_MONTH)
    db.execute(
        "UPDATE stg_esg_emissions SET scope1_tco2e = 220.0 WHERE as_of_month = :m AND investment_id = 'INV0000001'",
        m=AS_OF_MONTH,
    )
    esg_service.compute_waci(AS_OF_MONTH)
    # INV0000001 intensity becomes 300/50 = 6.0 -> 0.6*6 + 0.3*3 = 4.5
    assert approx_equal(_value(_metric_row(db, PORTFOLIO_MAIN)), Decimal("4.5"))


def test_rp47_13_portfolio_without_positions_gets_no_value(seeded_portfolios: EsgDb):
    """RP-47 AC (edge): a portfolio with no positions in the month yields no value (NULL or no row), never an error."""
    db = seeded_portfolios
    stage_emissions(db, MAIN_FEED_ROWS_2026_10)
    esg_service.compute_waci(AS_OF_MONTH)
    row = _metric_row(db, PORTFOLIO_NO_METRIC)
    assert row is None or _value(row) is None


def test_rp47_14_month_with_no_staging_data_yields_no_metrics(seeded_portfolios: EsgDb):
    """RP-47 AC (edge): computing a month with no staged emissions does not fabricate values."""
    db = seeded_portfolios
    metrics = esg_service.compute_waci("2025-01")
    assert all(_value(m) is None for m in metrics)
    for row in db.rows(f"SELECT * FROM {METRICS_TABLE} WHERE as_of_month = '2025-01'"):
        assert _value(row) is None
