"""Gap hunt (RP-47): as-of month handling, snapshot selection and coverage edge cases in sql/esg_waci_v1.sql."""
from datetime import date
from decimal import Decimal, ROUND_HALF_EVEN

import pytest

from models.esg import PortfolioEsgMetrics, StgEsgEmissions
from services.esg_service import compute_waci, load_esg_feed, set_override
from tests.esg.conftest import AS_OF, PORT_ID, add_portfolio, add_position, write_feed


def _metric(db, port_id=PORT_ID, month=AS_OF):
    return db.query(PortfolioEsgMetrics).filter_by(portfolio_id=port_id, as_of_month=month).one()


def test_position_opened_after_month_end_is_excluded(db, tmp_path):
    """RP-47: a holding whose only snapshot is dated after the as-of month end did not exist at month end
    and must not enter the weights, the total market value or the coverage for that month."""
    add_portfolio(db)
    add_position(db, "AAA", "1000", on=date(2026, 10, 31))
    add_position(db, "NEW", "1000", on=date(2026, 11, 1))
    load_esg_feed(db, write_feed(tmp_path, ["2026-10,AAA,100,0,10", "2026-10,NEW,9000,0,10"]))

    compute_waci(db, AS_OF)

    metric = _metric(db)
    assert float(metric.total_market_value) == pytest.approx(1000), "future-dated snapshot leaked into total_market_value"
    assert float(metric.waci_computed) == pytest.approx(10.0)
    assert float(metric.coverage_pct) == pytest.approx(100.0)


def test_holding_with_several_snapshots_is_counted_once(db, tmp_path):
    """RP-47: positions are dated snapshots; a holding with a prior-month and a current-month row must be
    weighted once (latest snapshot for the as-of month), not summed across snapshots."""
    add_portfolio(db)
    add_position(db, "AAA", "1000", on=date(2026, 9, 30))
    add_position(db, "AAA", "1200", on=date(2026, 10, 15))
    add_position(db, "AAA", "1300", on=date(2026, 10, 31))
    add_position(db, "BBB", "1300", on=date(2026, 10, 31))
    load_esg_feed(db, write_feed(tmp_path, ["2026-10,AAA,100,0,10", "2026-10,BBB,300,0,10"]))

    compute_waci(db, AS_OF)

    metric = _metric(db)
    assert float(metric.total_market_value) == pytest.approx(2600), "snapshots of the same holding were summed"
    assert float(metric.waci_computed) == pytest.approx((1300 * 10 + 1300 * 30) / 2600)


def test_holding_sold_mid_month_with_earlier_active_snapshot_is_excluded(db, tmp_path):
    """RP-47: a holding sold mid-month (active snapshot on the 1st, closed snapshot on the 15th) is not an
    active position at month end; the earlier active snapshot must not survive into the calculation."""
    add_portfolio(db)
    add_position(db, "AAA", "500", on=date(2026, 10, 31))
    add_position(db, "SOLD", "500", on=date(2026, 10, 1))
    add_position(db, "SOLD", "0", status="C", on=date(2026, 10, 15))
    load_esg_feed(db, write_feed(tmp_path, ["2026-10,AAA,100,0,10", "2026-10,SOLD,9000,0,10"]))

    compute_waci(db, AS_OF)

    metric = _metric(db)
    assert float(metric.total_market_value) == pytest.approx(500), "sold holding still weighted via its earlier snapshot"
    assert float(metric.waci_computed) == pytest.approx(10.0)


def test_rerun_after_position_change_reflects_new_snapshot_only(db, tmp_path):
    """RP-47: rerun is idempotent after a position change; the new snapshot replaces (not adds to) the old one."""
    add_portfolio(db)
    add_position(db, "AAA", "1000", on=date(2026, 10, 10))
    add_position(db, "BBB", "1000", on=date(2026, 10, 10))
    load_esg_feed(db, write_feed(tmp_path, ["2026-10,AAA,100,0,10", "2026-10,BBB,300,0,10"]))
    compute_waci(db, AS_OF)
    assert float(_metric(db).waci_computed) == pytest.approx(20.0)

    add_position(db, "AAA", "3000", on=date(2026, 10, 20))
    db.commit()
    compute_waci(db, AS_OF)

    rows = db.query(PortfolioEsgMetrics).filter_by(as_of_month=AS_OF).all()
    assert len(rows) == 1
    assert float(rows[0].total_market_value) == pytest.approx(4000)
    assert float(rows[0].waci_computed) == pytest.approx((3000 * 10 + 1000 * 30) / 4000)


def test_short_position_does_not_produce_negative_intensity(db, tmp_path):
    """RP-47: a negative market value (short) must never make WACI negative or push coverage above 100%."""
    add_portfolio(db)
    add_position(db, "LONG", "1000")
    add_position(db, "SHRT", "-400")
    load_esg_feed(db, write_feed(tmp_path, ["2026-10,LONG,100,0,10", "2026-10,SHRT,5000,0,10"]))

    compute_waci(db, AS_OF)

    metric = _metric(db)
    assert float(metric.waci_computed) >= 0
    assert 0 <= float(metric.coverage_pct) <= 100


def test_sql_result_matches_decimal_arithmetic_to_six_places(seeded_db, tmp_path):
    """RP-47 / RP-48: the REAL arithmetic in SQLite must agree with exact Decimal arithmetic at the 6 dp the
    API exposes (no drift between the SQL procedure and a Python recomputation)."""
    rows = [
        ("AAPL", Decimal("27787.50"), Decimal("55200"), Decimal("2780"), Decimal("391035")),
        ("MSFT", Decimal("37885.00"), Decimal("144960"), Decimal("393134"), Decimal("245122")),
        ("GOOGL", Decimal("10692.00"), Decimal("79400"), Decimal("2460000"), Decimal("350018")),
        ("TSLA", Decimal("49134.00"), Decimal("185000"), Decimal("310000"), Decimal("1.7")),
    ]
    load_esg_feed(seeded_db, write_feed(tmp_path, [f"2026-10,{i},{s1},{s2},{r}" for i, _, s1, s2, r in rows]))
    compute_waci(seeded_db, AS_OF)

    total = sum(mv for _, mv, *_ in rows)
    expected = sum(mv * (s1 + s2) / r for _, mv, s1, s2, r in rows) / total
    got = Decimal(str(_metric(seeded_db).waci_computed))
    assert got.quantize(Decimal("0.000001"), ROUND_HALF_EVEN) == expected.quantize(Decimal("0.000001"), ROUND_HALF_EVEN)


@pytest.mark.xfail(strict=True, reason="open: loader rejects blank revenue instead of staging NULL (spec 5.1 / acceptance test_rp46_03)")
def test_blank_revenue_is_staged_as_null_and_excluded_from_waci(db, tmp_path):
    """RP-47: 'holdings with missing revenue are excluded and counted against coverage' assumes a staging row
    with NULL revenue. The loader currently rejects the row, so the NULL-revenue branch of the SQL is unreachable
    from the feed and the provider sees a reject for a legitimate missing value."""
    add_portfolio(db)
    add_position(db, "AAA", "500")
    add_position(db, "NOREV", "500")
    result = load_esg_feed(db, write_feed(tmp_path, ["2026-10,AAA,100,0,10", "2026-10,NOREV,100,0,"]))

    assert result.rejected_rows == 0
    staged = db.query(StgEsgEmissions).filter_by(investment_id="NOREV").one()
    assert staged.revenue_musd is None

    compute_waci(db, AS_OF)
    metric = _metric(db)
    assert float(metric.waci_computed) == pytest.approx(5.0)
    assert float(metric.coverage_pct) == pytest.approx(50.0)


@pytest.mark.xfail(strict=True, reason="open: computing a month with no staged data writes NULL rows that become the 'current' month")
def test_month_without_staged_data_does_not_become_current_metric(seeded_db, tmp_path):
    """RP-47 / RP-48: running the procedure for a month with no staged emissions (for example a month whose file
    has not arrived yet) must not produce an empty metric that hides the latest real month and its override
    from GET /esg (which picks the greatest as_of_month)."""
    load_esg_feed(seeded_db, write_feed(tmp_path, ["2026-10,AAPL,100,0,10"]))
    compute_waci(seeded_db, AS_OF)
    set_override(seeded_db, PORT_ID, Decimal("7.5"), "Provider restated scope 2 figures", "pm_user")

    compute_waci(seeded_db, "2026-12")

    from services.esg_service import get_current_metric
    current = get_current_metric(seeded_db, PORT_ID)
    assert current.as_of_month == AS_OF, f"empty month {current.as_of_month} masked the latest computed month"
    assert current.effective_value == Decimal("7.5")
