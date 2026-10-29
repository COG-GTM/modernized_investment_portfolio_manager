"""RP-50: Override with a reason."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from tests.esg.conftest import (
    ACCOUNT_MAIN,
    ACCOUNT_NO_METRIC,
    ACCOUNT_UNKNOWN,
    AS_OF_MONTH,
    EXPECTED_WACI_MAIN,
    NEXT_MONTH,
    OVERRIDE_ROUTE,
    PORTFOLIO_MAIN,
    EsgDb,
    approx_equal,
    error_text,
    esg_url,
    insert_metric,
    put_override,
    require_route,
)

pytestmark = [pytest.mark.esg, pytest.mark.rp50]

VALID_REASON = "Issuer restated scope 2 figures"
VALIDATION_STATUSES = (400, 422)


@pytest.fixture(autouse=True)
def _override_route_present():
    require_route(OVERRIDE_ROUTE, "PUT", "RP-50")


@pytest.fixture
def metric(seeded_portfolios: EsgDb) -> EsgDb:
    insert_metric(seeded_portfolios, PORTFOLIO_MAIN)
    return seeded_portfolios


def test_rp50_01_valid_override_is_applied(client, metric: EsgDb):
    """RP-50 AC: PUT /api/portfolio/{account_number}/esg/override with value and reason applies the override."""
    response = put_override(client, ACCOUNT_MAIN, 2.75, VALID_REASON)
    assert response.status_code in (200, 201), response.text
    body = client.get(esg_url(ACCOUNT_MAIN)).json()
    assert body["source"] == "override"
    assert approx_equal(body["effective_value"], Decimal("2.75"))
    assert approx_equal(body["computed_value"], EXPECTED_WACI_MAIN)


def test_rp50_02_put_response_reflects_new_state(client, metric: EsgDb):
    """RP-50 AC (edge): the PUT response itself describes the overridden metric so the UI can refresh without a second call."""
    body = put_override(client, ACCOUNT_MAIN, 2.75, VALID_REASON).json()
    assert body.get("source") == "override"
    assert approx_equal(body.get("effective_value"), Decimal("2.75"))
    assert body.get("as_of_month") == AS_OF_MONTH


def test_rp50_03_reason_is_mandatory(client, metric: EsgDb):
    """RP-50 AC: reason mandatory."""
    response = put_override(client, ACCOUNT_MAIN, 2.75, None)
    assert response.status_code in VALIDATION_STATUSES, response.text
    assert "reason" in error_text(response)
    assert client.get(esg_url(ACCOUNT_MAIN)).json()["source"] == "computed"


@pytest.mark.parametrize("reason", ["", "   ", "too short", "123456789"], ids=["empty", "blank", "9-chars-text", "9-chars-digits"])
def test_rp50_04_reason_shorter_than_10_characters_is_rejected(client, metric: EsgDb, reason: str):
    """RP-50 AC: reason minimum 10 characters."""
    response = put_override(client, ACCOUNT_MAIN, 2.75, reason)
    assert response.status_code in VALIDATION_STATUSES, response.text
    assert "reason" in error_text(response)


def test_rp50_05_reason_of_exactly_10_characters_is_accepted(client, metric: EsgDb):
    """RP-50 AC (boundary): a 10-character reason is the minimum and must be accepted."""
    response = put_override(client, ACCOUNT_MAIN, 2.75, "1234567890")
    assert response.status_code in (200, 201), response.text


@pytest.mark.parametrize("value", [-0.01, -1, -1000], ids=["-0.01", "-1", "-1000"])
def test_rp50_06_negative_value_is_rejected(client, metric: EsgDb, value: float):
    """RP-50 AC: value non-negative."""
    response = put_override(client, ACCOUNT_MAIN, value, VALID_REASON)
    assert response.status_code in VALIDATION_STATUSES, response.text
    assert "value" in error_text(response)
    assert client.get(esg_url(ACCOUNT_MAIN)).json()["source"] == "computed"


def test_rp50_07_zero_value_is_accepted(client, metric: EsgDb):
    """RP-50 AC (boundary): zero is non-negative and a legitimate override (for example a fully divested green mandate)."""
    response = put_override(client, ACCOUNT_MAIN, 0, VALID_REASON)
    assert response.status_code in (200, 201), response.text
    body = client.get(esg_url(ACCOUNT_MAIN)).json()
    assert body["source"] == "override"
    assert float(body["effective_value"]) == 0


def test_rp50_08_value_is_mandatory_and_must_be_numeric(client, metric: EsgDb):
    """RP-50 AC (edge): missing or non-numeric value is a validation error, not a 500."""
    missing = put_override(client, ACCOUNT_MAIN, None, VALID_REASON)
    assert missing.status_code in VALIDATION_STATUSES
    non_numeric = put_override(client, ACCOUNT_MAIN, "three point one", VALID_REASON)
    assert non_numeric.status_code in VALIDATION_STATUSES


def test_rp50_09_override_applies_to_current_as_of_month_only(client, metric: EsgDb):
    """RP-50 AC: an override applies to the current as-of month only; a newer month's metric is not overridden."""
    put_override(client, ACCOUNT_MAIN, 2.75, VALID_REASON)
    before = client.get(esg_url(ACCOUNT_MAIN)).json()
    assert before["as_of_month"] == AS_OF_MONTH and before["source"] == "override"

    insert_metric(
        metric,
        PORTFOLIO_MAIN,
        as_of_month=NEXT_MONTH,
        computed_value=Decimal("3.075"),
        coverage_pct=Decimal("100"),
        computed_at=datetime(2026, 12, 1, 2, 0, 0),
    )
    after = client.get(esg_url(ACCOUNT_MAIN)).json()
    assert after["as_of_month"] == NEXT_MONTH
    assert after["source"] == "computed"
    assert approx_equal(after["effective_value"], Decimal("3.075"))
    assert after.get("override") in (None, {})


def test_rp50_10_override_cannot_target_another_month(client, metric: EsgDb):
    """RP-50 AC: a request body naming a different as_of_month is rejected or ignored; only the current month is overridable."""
    response = client.put(
        f"/api/portfolio/{ACCOUNT_MAIN}/esg/override",
        json={"value": 2.75, "reason": VALID_REASON, "as_of_month": "2025-01"},
        headers={"X-User": "pm_jane"},
    )
    if response.status_code in (200, 201):
        body = client.get(esg_url(ACCOUNT_MAIN)).json()
        assert body["as_of_month"] == AS_OF_MONTH
        assert body["source"] == "override"
    else:
        assert response.status_code in (400, 409, 422)
        assert client.get(esg_url(ACCOUNT_MAIN)).json()["source"] == "computed"


def test_rp50_11_second_override_replaces_the_first(client, metric: EsgDb):
    """RP-50 AC (edge): overriding twice leaves the latest value effective."""
    put_override(client, ACCOUNT_MAIN, 2.75, VALID_REASON)
    put_override(client, ACCOUNT_MAIN, 2.5, "Second correction after reviewing vendor file")
    body = client.get(esg_url(ACCOUNT_MAIN)).json()
    assert approx_equal(body["effective_value"], Decimal("2.5"))
    assert body["override"]["reason"] == "Second correction after reviewing vendor file"


def test_rp50_12_unknown_account_returns_404(client, metric: EsgDb):
    """RP-50 AC (edge): overriding an unknown account is a 404."""
    response = put_override(client, ACCOUNT_UNKNOWN, 2.75, VALID_REASON)
    assert response.status_code == 404


def test_rp50_13_override_without_a_computed_month_is_rejected(client, seeded_portfolios: EsgDb):
    """RP-50 AC (edge): with no current as-of month there is nothing to override - 404 or 409, never a silent success."""
    response = put_override(client, ACCOUNT_NO_METRIC, 2.75, VALID_REASON)
    assert response.status_code in (404, 409, 422), response.text


def test_rp50_14_validation_error_body_is_renderable(client, metric: EsgDb):
    """RP-50 AC: validation errors are returned (and shown by the UI) - the body must say which field failed."""
    response = put_override(client, ACCOUNT_MAIN, -1, "short")
    assert response.status_code in VALIDATION_STATUSES
    text = error_text(response)
    assert "reason" in text and "value" in text


def test_rp50_15_reason_is_trimmed_before_length_check(client, metric: EsgDb):
    """RP-50 AC (edge): padding a short reason with whitespace does not satisfy the 10-character minimum."""
    response = put_override(client, ACCOUNT_MAIN, 2.75, "   short   ")
    assert response.status_code in VALIDATION_STATUSES
