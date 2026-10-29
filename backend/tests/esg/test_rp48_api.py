"""RP-48: Expose carbon intensity through the portfolio API."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from tests.esg.conftest import (
    ACCOUNT_MAIN,
    ACCOUNT_NO_METRIC,
    ACCOUNT_UNKNOWN,
    ACCOUNT_ZERO_MV,
    AS_OF_MONTH,
    ESG_ROUTE,
    EXPECTED_COVERAGE_MAIN,
    EXPECTED_WACI_MAIN,
    NEXT_MONTH,
    OVERRIDE_ROUTE,
    PORTFOLIO_MAIN,
    PORTFOLIO_ZERO_MV,
    EsgDb,
    approx_equal,
    esg_url,
    insert_metric,
    put_override,
    require_route,
)

pytestmark = [pytest.mark.esg, pytest.mark.rp48]

RESPONSE_FIELDS = {"as_of_month", "computed_value", "effective_value", "source", "coverage_pct"}


@pytest.fixture(autouse=True)
def _esg_route_present():
    require_route(ESG_ROUTE, "GET", "RP-48")


def test_rp48_01_returns_computed_metric_for_known_account(client, seeded_portfolios: EsgDb):
    """RP-48 AC: GET /api/portfolio/{account_number}/esg returns as_of_month, computed_value, effective_value, source, coverage_pct."""
    insert_metric(seeded_portfolios, PORTFOLIO_MAIN)
    response = client.get(esg_url(ACCOUNT_MAIN))
    assert response.status_code == 200, response.text
    body = response.json()
    assert RESPONSE_FIELDS <= set(body), f"missing fields: {RESPONSE_FIELDS - set(body)}"
    assert body["as_of_month"] == AS_OF_MONTH
    assert approx_equal(body["computed_value"], EXPECTED_WACI_MAIN)
    assert approx_equal(body["effective_value"], EXPECTED_WACI_MAIN)
    assert body["source"] == "computed"
    assert approx_equal(body["coverage_pct"], EXPECTED_COVERAGE_MAIN, Decimal("0.05"))


def test_rp48_02_override_details_absent_when_not_overridden(client, seeded_portfolios: EsgDb):
    """RP-48 AC: override details are only present when an override exists."""
    insert_metric(seeded_portfolios, PORTFOLIO_MAIN)
    body = client.get(esg_url(ACCOUNT_MAIN)).json()
    assert body.get("override") in (None, {})


def test_rp48_03_unknown_account_returns_404(client, seeded_portfolios: EsgDb):
    """RP-48 AC: 404 for unknown account."""
    response = client.get(esg_url(ACCOUNT_UNKNOWN))
    assert response.status_code == 404
    detail = str(response.json()).lower()
    assert "account" in detail or "portfolio" in detail


def test_rp48_04_known_account_without_metric_returns_empty_payload(client, seeded_portfolios: EsgDb):
    """RP-48 / RP-49 AC: a known account with no computed metric returns 200 with null values so the dashboard can show its empty state."""
    response = client.get(esg_url(ACCOUNT_NO_METRIC))
    assert response.status_code == 200, (
        "known account with no metric must not be confused with an unknown account (404)"
    )
    body = response.json()
    assert body.get("computed_value") is None
    assert body.get("effective_value") is None
    assert body.get("override") in (None, {})


def test_rp48_05_latest_as_of_month_is_returned(client, seeded_portfolios: EsgDb):
    """RP-48 AC (edge): when several months exist, the most recent as-of month is returned."""
    insert_metric(seeded_portfolios, PORTFOLIO_MAIN, as_of_month=AS_OF_MONTH, computed_value=Decimal("3.3"))
    insert_metric(
        seeded_portfolios,
        PORTFOLIO_MAIN,
        as_of_month=NEXT_MONTH,
        computed_value=Decimal("3.075"),
        coverage_pct=Decimal("100"),
        computed_at=datetime(2026, 12, 1, 2, 0, 0),
    )
    body = client.get(esg_url(ACCOUNT_MAIN)).json()
    assert body["as_of_month"] == NEXT_MONTH
    assert approx_equal(body["computed_value"], Decimal("3.075"))


def test_rp48_06_zero_market_value_portfolio_returns_null_value(client, seeded_portfolios: EsgDb):
    """RP-48 AC (edge): a metric row with NULL value (zero market value) is returned as null, not 0 or an error."""
    insert_metric(seeded_portfolios, PORTFOLIO_ZERO_MV, computed_value=None, coverage_pct=Decimal("0"))
    response = client.get(esg_url(ACCOUNT_ZERO_MV))
    assert response.status_code == 200
    body = response.json()
    assert body["computed_value"] is None
    assert body["effective_value"] is None
    assert float(body["coverage_pct"]) == 0


def test_rp48_07_source_and_override_block_after_override(client, seeded_portfolios: EsgDb):
    """RP-48 AC: source is 'override' and override details (value, reason, who, when) are present when an override exists."""
    require_route(OVERRIDE_ROUTE, "PUT", "RP-48")
    insert_metric(seeded_portfolios, PORTFOLIO_MAIN)
    put = put_override(client, ACCOUNT_MAIN, 2.75, "Issuer restated scope 2 figures")
    assert put.status_code in (200, 201), put.text

    body = client.get(esg_url(ACCOUNT_MAIN)).json()
    assert body["source"] == "override"
    assert approx_equal(body["computed_value"], EXPECTED_WACI_MAIN), "computed_value must survive an override"
    assert approx_equal(body["effective_value"], Decimal("2.75"))
    override = body.get("override")
    assert override, "override details must be present"
    assert approx_equal(override.get("value"), Decimal("2.75"))
    assert override.get("reason") == "Issuer restated scope 2 figures"
    who = override.get("overridden_by") or override.get("who") or override.get("user")
    when = override.get("overridden_at") or override.get("when") or override.get("timestamp")
    assert who == "pm_jane"
    assert when


def test_rp48_08_invalid_account_format_is_not_a_server_error(client, seeded_portfolios: EsgDb):
    """RP-48 AC (edge): a malformed account number yields 400/404/422, never a 500."""
    response = client.get(esg_url("not-an-account"))
    assert response.status_code in (400, 404, 422)


def test_rp48_09_account_number_is_echoed_or_consistent(client, seeded_portfolios: EsgDb):
    """RP-48 AC (edge): if the payload carries an account or portfolio identifier it matches the request."""
    insert_metric(seeded_portfolios, PORTFOLIO_MAIN)
    body = client.get(esg_url(ACCOUNT_MAIN)).json()
    if "account_number" in body or "accountNumber" in body:
        assert body.get("account_number", body.get("accountNumber")) == ACCOUNT_MAIN
    if "portfolio_id" in body:
        assert body["portfolio_id"] == PORTFOLIO_MAIN
