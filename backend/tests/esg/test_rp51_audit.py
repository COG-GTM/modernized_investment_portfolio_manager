"""RP-51: Audit trail."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.exc import DBAPIError, OperationalError, IntegrityError

from tests.esg.conftest import (
    ACCOUNT_MAIN,
    ACCOUNT_UNKNOWN,
    AS_OF_MONTH,
    AUDIT_ROUTE,
    AUDIT_TABLE,
    EXPECTED_WACI_MAIN,
    OVERRIDE_ROUTE,
    PORTFOLIO_MAIN,
    EsgDb,
    approx_equal,
    audit_rows,
    audit_url,
    clear_override,
    esg_url,
    insert_metric,
    normalise_audit,
    put_override,
    require_route,
)

pytestmark = [pytest.mark.esg, pytest.mark.rp51]

REASON_1 = "Issuer restated scope 2 figures"
REASON_2 = "Second correction after reviewing vendor file"
CLEAR_REASON = "Vendor file corrected, reverting to computed value"


@pytest.fixture(autouse=True)
def _routes_present():
    require_route(OVERRIDE_ROUTE, "PUT", "RP-51")
    require_route(AUDIT_ROUTE, "GET", "RP-51")


@pytest.fixture
def metric(seeded_portfolios: EsgDb) -> EsgDb:
    insert_metric(seeded_portfolios, PORTFOLIO_MAIN)
    return seeded_portfolios


def test_rp51_01_audit_table_has_required_columns(metric: EsgDb):
    """RP-51 AC: table esg_override_audit carries who, when, old value, new value, reason, as_of_month."""
    metric.require_table(AUDIT_TABLE, "RP-51")
    cols = {c.lower() for c in metric.columns(AUDIT_TABLE)}
    sample = normalise_audit({c: None for c in cols})
    for canonical in ("who", "when", "old_value", "new_value", "reason", "as_of_month"):
        assert canonical in sample, f"no column for '{canonical}' in {sorted(cols)}"


def test_rp51_02_override_writes_an_audit_row(client, metric: EsgDb):
    """RP-51 AC: an override writes who, when, old value, new value, reason and as_of_month."""
    put_override(client, ACCOUNT_MAIN, 2.75, REASON_1)
    rows = audit_rows(metric, PORTFOLIO_MAIN)
    assert len(rows) == 1
    row = rows[0]
    assert row["who"] == "pm_jane"
    assert row["when"]
    assert approx_equal(row["old_value"], EXPECTED_WACI_MAIN), "old value is the previously effective (computed) value"
    assert approx_equal(row["new_value"], Decimal("2.75"))
    assert row["reason"] == REASON_1
    assert row["as_of_month"] == AS_OF_MONTH


def test_rp51_03_second_override_records_previous_override_as_old_value(client, metric: EsgDb):
    """RP-51 AC (edge): old value of the second row is the first override, not the computed value."""
    put_override(client, ACCOUNT_MAIN, 2.75, REASON_1)
    put_override(client, ACCOUNT_MAIN, 2.5, REASON_2)
    rows = audit_rows(metric, PORTFOLIO_MAIN)
    assert len(rows) == 2
    assert approx_equal(rows[1]["old_value"], Decimal("2.75"))
    assert approx_equal(rows[1]["new_value"], Decimal("2.5"))


def test_rp51_04_clearing_an_override_writes_a_new_audit_row(client, metric: EsgDb):
    """RP-51 AC: clearing an override writes a new audit row (new value null) and restores the computed value."""
    put_override(client, ACCOUNT_MAIN, 2.75, REASON_1)
    response = clear_override(client, ACCOUNT_MAIN, CLEAR_REASON)
    assert response.status_code in (200, 204), response.text

    body = client.get(esg_url(ACCOUNT_MAIN)).json()
    assert body["source"] == "computed"
    assert approx_equal(body["effective_value"], EXPECTED_WACI_MAIN)

    rows = audit_rows(metric, PORTFOLIO_MAIN)
    assert len(rows) == 2
    cleared = rows[-1]
    assert approx_equal(cleared["old_value"], Decimal("2.75"))
    assert cleared["new_value"] is None
    assert cleared["reason"] == CLEAR_REASON
    assert cleared["who"] == "pm_jane"


def test_rp51_05_audit_is_append_only_rows_are_never_rewritten(client, metric: EsgDb):
    """RP-51 AC: append-only - earlier rows are unchanged after later overrides and clears."""
    put_override(client, ACCOUNT_MAIN, 2.75, REASON_1)
    first_snapshot = audit_rows(metric, PORTFOLIO_MAIN)[0]
    put_override(client, ACCOUNT_MAIN, 2.5, REASON_2)
    clear_override(client, ACCOUNT_MAIN, CLEAR_REASON)
    rows = audit_rows(metric, PORTFOLIO_MAIN)
    assert len(rows) == 3
    assert rows[0] == first_snapshot


def test_rp51_06_audit_table_rejects_updates_and_deletes(client, metric: EsgDb):
    """RP-51 AC: append-only is enforced in the database (trigger or constraint), not only by convention."""
    put_override(client, ACCOUNT_MAIN, 2.75, REASON_1)
    with pytest.raises((OperationalError, IntegrityError, DBAPIError)):
        metric.execute(f"UPDATE {AUDIT_TABLE} SET reason = 'tampered'")
    with pytest.raises((OperationalError, IntegrityError, DBAPIError)):
        metric.execute(f"DELETE FROM {AUDIT_TABLE}")
    assert audit_rows(metric, PORTFOLIO_MAIN)[0]["reason"] == REASON_1


def test_rp51_07_audit_endpoint_lists_history_newest_first(client, metric: EsgDb):
    """RP-51 AC: GET /api/portfolio/{account_number}/esg/audit lists history newest first."""
    put_override(client, ACCOUNT_MAIN, 2.75, REASON_1)
    put_override(client, ACCOUNT_MAIN, 2.5, REASON_2)
    clear_override(client, ACCOUNT_MAIN, CLEAR_REASON)

    response = client.get(audit_url(ACCOUNT_MAIN))
    assert response.status_code == 200, response.text
    body = response.json()
    items = body if isinstance(body, list) else body.get("items") or body.get("history") or body.get("audit")
    assert isinstance(items, list) and len(items) == 3
    items = [normalise_audit(i) for i in items]
    assert [i["reason"] for i in items] == [CLEAR_REASON, REASON_2, REASON_1]
    assert items[0]["new_value"] is None
    assert approx_equal(items[-1]["old_value"], EXPECTED_WACI_MAIN)
    for item in items:
        for key in ("who", "when", "reason", "as_of_month"):
            assert item.get(key) not in (None, ""), f"audit item missing {key}: {item}"


def test_rp51_08_audit_endpoint_empty_for_account_without_history(client, metric: EsgDb):
    """RP-51 AC (edge): an account with no overrides returns an empty list, not 404."""
    response = client.get(audit_url(ACCOUNT_MAIN))
    assert response.status_code == 200
    body = response.json()
    items = body if isinstance(body, list) else body.get("items") or body.get("history") or body.get("audit") or []
    assert items == []


def test_rp51_09_audit_endpoint_404_for_unknown_account(client, metric: EsgDb):
    """RP-51 AC (edge): unknown account is a 404 on the audit endpoint too."""
    assert client.get(audit_url(ACCOUNT_UNKNOWN)).status_code == 404


def test_rp51_10_failed_override_leaves_no_audit_row(client, metric: EsgDb):
    """RP-51 AC (edge): a rejected override (validation error) must not leave an audit row behind."""
    put_override(client, ACCOUNT_MAIN, -1, "short")
    assert audit_rows(metric, PORTFOLIO_MAIN) == []


def test_rp51_11_clearing_when_nothing_is_overridden_is_a_no_op_or_conflict(client, metric: EsgDb):
    """RP-51 AC (edge): clearing with no active override must not write a misleading audit row."""
    response = clear_override(client, ACCOUNT_MAIN, CLEAR_REASON)
    assert response.status_code in (200, 204, 404, 409)
    assert audit_rows(metric, PORTFOLIO_MAIN) == []


def test_rp51_12_audit_rows_identify_the_month_they_apply_to(client, metric: EsgDb):
    """RP-51 AC: as_of_month is stored on every audit row so history survives month roll-over."""
    put_override(client, ACCOUNT_MAIN, 2.75, REASON_1)
    assert {r["as_of_month"] for r in audit_rows(metric, PORTFOLIO_MAIN)} == {AS_OF_MONTH}
