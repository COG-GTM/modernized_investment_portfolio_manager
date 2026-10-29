"""RP-49: Show carbon intensity on the portfolio dashboard.

The component behaviour (effective value with unit, as-of month, coverage,
override indicator, empty state) is covered by
src/components/__tests__/CarbonIntensityCard.test.tsx (vitest). The tests here
pin down the API payload the dashboard renders from, so a backend change cannot
break the dashboard states silently.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from tests.esg.conftest import (
    ACCOUNT_MAIN,
    ACCOUNT_NO_METRIC,
    AS_OF_MONTH,
    ESG_ROUTE,
    OVERRIDE_ROUTE,
    PORTFOLIO_MAIN,
    EsgDb,
    esg_url,
    insert_metric,
    put_override,
    require_route,
)

pytestmark = [pytest.mark.esg, pytest.mark.rp49]


@pytest.fixture(autouse=True)
def _esg_route_present():
    require_route(ESG_ROUTE, "GET", "RP-49")


def test_rp49_01_payload_carries_everything_the_card_displays(client, seeded_portfolios: EsgDb):
    """RP-49 AC: dashboard shows effective value with unit, as-of month and coverage - all derivable from the payload."""
    insert_metric(seeded_portfolios, PORTFOLIO_MAIN)
    body = client.get(esg_url(ACCOUNT_MAIN)).json()
    assert isinstance(body["effective_value"], (int, float))
    assert body["as_of_month"] == AS_OF_MONTH
    assert isinstance(body["coverage_pct"], (int, float))
    unit = body.get("unit")
    if unit is not None:
        assert "tco2e" in unit.lower() and ("$m" in unit.lower() or "musd" in unit.lower() or "million" in unit.lower())


def test_rp49_02_empty_state_is_distinguishable_from_error(client, seeded_portfolios: EsgDb):
    """RP-49 AC: empty state when no metric exists - 200 with null effective_value, not an error status."""
    response = client.get(esg_url(ACCOUNT_NO_METRIC))
    assert response.status_code == 200
    assert response.json()["effective_value"] is None


def test_rp49_03_override_indicator_is_driven_by_source_field(client, seeded_portfolios: EsgDb):
    """RP-49 AC: an indicator is shown when the value is an override - the payload flags it via source == 'override'."""
    require_route(OVERRIDE_ROUTE, "PUT", "RP-49")
    insert_metric(seeded_portfolios, PORTFOLIO_MAIN)
    assert client.get(esg_url(ACCOUNT_MAIN)).json()["source"] == "computed"
    put_override(client, ACCOUNT_MAIN, 1.5, "Manual correction after data vendor notice")
    body = client.get(esg_url(ACCOUNT_MAIN)).json()
    assert body["source"] == "override"
    assert body["effective_value"] == pytest.approx(1.5)
    assert body["computed_value"] == pytest.approx(float(Decimal("3.3")))
