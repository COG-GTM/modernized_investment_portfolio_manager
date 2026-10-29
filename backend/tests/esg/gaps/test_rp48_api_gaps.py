"""Gap hunt (RP-48): GET /api/portfolio/{account_number}/esg contract edge cases."""
from decimal import Decimal

import pytest

from services.esg_service import compute_waci, load_esg_feed, set_override
from tests.esg.conftest import ACCOUNT, AS_OF, PORT_ID, add_portfolio, add_position, write_feed


@pytest.mark.xfail(strict=True, reason="open: known account without a metric returns 404, indistinguishable from an unknown account")
def test_known_account_without_metric_is_not_a_404(client):
    """RP-48: 404 is reserved for an unknown account. A known account that simply has no metric yet must be
    distinguishable (200 with null values, or a dedicated status) so the dashboard empty state is not confused
    with a bad account number."""
    unknown = client.get("/api/portfolio/9999999999/esg")
    known_no_metric = client.get(f"/api/portfolio/{ACCOUNT}/esg")
    assert unknown.status_code == 404
    assert known_no_metric.status_code != 404, known_no_metric.text


def test_override_survives_recompute_and_computed_value_is_refreshed(client, seeded_db, tmp_path):
    """RP-48 / RP-50: after an override, a recompute of the same month must keep the override as the effective
    value while exposing the refreshed computed value, so the reader can see the override is now stale."""
    load_esg_feed(seeded_db, write_feed(tmp_path, ["2026-10,AAPL,100,0,10"], name="v1.csv"))
    compute_waci(seeded_db, AS_OF)
    set_override(seeded_db, PORT_ID, Decimal("7.5"), "Provider restated scope 2 figures", "pm_user")

    load_esg_feed(seeded_db, write_feed(tmp_path, ["2026-10,AAPL,200,0,10"], name="v2.csv"))
    compute_waci(seeded_db, AS_OF)

    body = client.get(f"/api/portfolio/{ACCOUNT}/esg").json()
    assert body["source"] == "override"
    assert body["effective_value"] == 7.5
    assert body["computed_value"] == pytest.approx(27787.5 * 20 / 125498.5)


def test_metric_for_earlier_month_is_not_hidden_by_later_month_without_positions(db, client, tmp_path):
    """RP-47 / RP-48: a portfolio that had positions only in October must still report October when the
    procedure is also run for November; the API picks the greatest as_of_month."""
    add_portfolio(db, port_id="PF-GAP01", account_no="2222222222")
    add_position(db, "AAA", "1000", port_id="PF-GAP01")
    load_esg_feed(db, write_feed(tmp_path, ["2026-10,AAA,100,0,10", "2026-11,AAA,100,0,10"]))
    compute_waci(db, AS_OF)
    body = client.get("/api/portfolio/2222222222/esg").json()
    assert body["as_of_month"] == AS_OF
    assert body["computed_value"] == pytest.approx(10.0)
