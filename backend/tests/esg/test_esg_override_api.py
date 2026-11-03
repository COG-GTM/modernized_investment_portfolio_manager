"""RP-50: PUT/DELETE /api/portfolio/{account_number}/esg/override."""
import json

import pytest

from models.esg import PortfolioEsgOverride
from tests.conftest import make_metric, make_portfolio

ACCOUNT = "1234567890"
URL = f"/api/portfolio/{ACCOUNT}/esg/override"
REASON = "Provider revenue for TSLA restated; aligned to Q3 filing."


@pytest.fixture
def seeded(session):
    make_portfolio(session)
    make_metric(session)
    return session


def _messages(response):
    return {tuple(e["loc"]): e["msg"] for e in response.json()["detail"]}


class TestSetOverride:
    def test_set_override_returns_override_state(self, client, seeded):
        response = client.put(URL, json={"value": 70.0, "reason": REASON, "changedBy": "PMJONES"})

        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "override"
        assert body["effectiveValue"] == 70.0
        assert body["computedValue"] == 64.137484
        assert body["asOfMonth"] == "2026-10"
        assert body["override"]["value"] == 70.0
        assert body["override"]["reason"] == REASON
        assert body["override"]["overriddenBy"] == "PMJONES"

    def test_get_reflects_override(self, client, seeded):
        client.put(URL, json={"value": 70.0, "reason": REASON})

        body = client.get(f"/api/portfolio/{ACCOUNT}/esg").json()
        assert body["source"] == "override"
        assert body["effectiveValue"] == 70.0
        assert body["override"]["overriddenBy"] == "SYSTEM"

    def test_replacing_override_keeps_one_row(self, client, seeded):
        client.put(URL, json={"value": 70.0, "reason": REASON})
        response = client.put(URL, json={"value": 55.5, "reason": "Second look after provider call."})

        assert response.json()["effectiveValue"] == 55.5
        assert seeded.query(PortfolioEsgOverride).count() == 1

    def test_zero_is_a_valid_value(self, client, seeded):
        response = client.put(URL, json={"value": 0, "reason": REASON})
        assert response.status_code == 200
        assert response.json()["effectiveValue"] == 0.0

    def test_reason_is_stored_trimmed(self, client, seeded):
        client.put(URL, json={"value": 1, "reason": f"   {REASON}   "})
        assert seeded.query(PortfolioEsgOverride).one().reason == REASON

    def test_applies_to_current_month_only(self, client, session):
        make_portfolio(session)
        make_metric(session, as_of_month="2026-09", computed_value="50")
        make_metric(session, as_of_month="2026-10")

        client.put(URL, json={"value": 70.0, "reason": REASON})

        rows = session.query(PortfolioEsgOverride).all()
        assert [(r.port_id, r.as_of_month) for r in rows] == [("PF-12345", "2026-10")]

    def test_client_cannot_choose_month(self, client, session):
        make_portfolio(session)
        make_metric(session, as_of_month="2026-09", computed_value="50")
        make_metric(session, as_of_month="2026-10")

        response = client.put(URL, json={"value": 70.0, "reason": REASON, "asOfMonth": "2026-09"})

        assert response.json()["asOfMonth"] == "2026-10"
        assert session.query(PortfolioEsgOverride).one().as_of_month == "2026-10"


    def test_concurrent_first_override_replaces_instead_of_500(self, client, seeded, monkeypatch):
        from datetime import datetime
        from decimal import Decimal
        from services import esg_service

        seeded.add(PortfolioEsgOverride(port_id="PF-12345", as_of_month="2026-10", override_value=Decimal("10"),
                                        reason="Inserted by a concurrent request.", overridden_by="OTHER",
                                        overridden_at=datetime(2026, 10, 30)))
        seeded.commit()
        real_override_for = esg_service._override_for
        calls = {"n": 0}

        def stale_then_real(db, port_id, as_of_month):
            calls["n"] += 1
            return None if calls["n"] == 1 else real_override_for(db, port_id, as_of_month)

        monkeypatch.setattr(esg_service, "_override_for", stale_then_real)

        response = client.put(URL, json={"value": 70.0, "reason": REASON, "changedBy": "PMJONES"})

        assert response.status_code == 200
        assert response.json()["override"]["overriddenBy"] == "PMJONES"
        seeded.expire_all()
        assert seeded.query(PortfolioEsgOverride).one().override_value == Decimal("70.000000")


class TestValidation:
    @pytest.mark.parametrize("reason", ["", "too short", "         x", "  123456789  "])
    def test_reason_shorter_than_10_characters_is_422(self, client, seeded, reason):
        response = client.put(URL, json={"value": 70.0, "reason": reason})

        assert response.status_code == 422
        assert _messages(response)[("body", "reason")] == "Value error, Reason must be at least 10 characters"

    def test_reason_of_exactly_10_characters_is_accepted(self, client, seeded):
        assert client.put(URL, json={"value": 70.0, "reason": "1234567890"}).status_code == 200

    def test_missing_reason_is_422(self, client, seeded):
        response = client.put(URL, json={"value": 70.0})
        assert response.status_code == 422
        assert ("body", "reason") in _messages(response)

    def test_negative_value_is_422(self, client, seeded):
        response = client.put(URL, json={"value": -0.01, "reason": REASON})

        assert response.status_code == 422
        assert _messages(response)[("body", "value")] == "Input should be greater than or equal to 0"

    def test_missing_value_is_422(self, client, seeded):
        assert client.put(URL, json={"reason": REASON}).status_code == 422

    @pytest.mark.parametrize("value", [True, "70", None])
    def test_non_numeric_value_is_422(self, client, seeded, value):
        assert client.put(URL, json={"value": value, "reason": REASON}).status_code == 422

    @pytest.mark.parametrize("raw", ["NaN", "Infinity", "-Infinity"])
    def test_non_finite_value_is_422_not_500(self, client, seeded, raw):
        payload = '{"value": %s, "reason": "%s"}' % (raw, REASON)
        response = client.put(URL, content=payload, headers={"Content-Type": "application/json"})

        assert response.status_code == 422
        json.loads(response.text)

    def test_both_errors_reported_together(self, client, seeded):
        response = client.put(URL, json={"value": -1, "reason": "short"})
        assert set(_messages(response)) == {("body", "value"), ("body", "reason")}

    def test_changed_by_longer_than_8_is_422(self, client, seeded):
        response = client.put(URL, json={"value": 1, "reason": REASON, "changedBy": "TOOLONGUSER"})
        assert response.status_code == 422

    def test_failed_validation_writes_nothing(self, client, seeded):
        client.put(URL, json={"value": -1, "reason": REASON})
        assert seeded.query(PortfolioEsgOverride).count() == 0


class TestStateErrors:
    def test_unknown_account_is_404(self, client, seeded):
        response = client.put("/api/portfolio/9999999999/esg/override", json={"value": 1, "reason": REASON})
        assert response.status_code == 404
        assert response.json() == {"detail": "Account not found"}

    def test_no_metric_yet_is_409(self, client, session):
        make_portfolio(session)

        response = client.put(URL, json={"value": 1, "reason": REASON})

        assert response.status_code == 409
        assert response.json() == {"detail": "No ESG metric exists for this account yet"}

    def test_no_position_month_is_409(self, client, session):
        make_portfolio(session)
        make_metric(session, computed_value=None, coverage_pct="0", positions_total=0)

        assert client.put(URL, json={"value": 1, "reason": REASON}).status_code == 409


class TestClearOverride:
    def test_clear_returns_computed_state(self, client, seeded):
        client.put(URL, json={"value": 70.0, "reason": REASON})

        response = client.request("DELETE", URL, json={"reason": "Provider corrected the file."})

        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "computed"
        assert body["effectiveValue"] == 64.137484
        assert body["override"] is None
        assert seeded.query(PortfolioEsgOverride).count() == 0

    def test_clear_requires_reason(self, client, seeded):
        client.put(URL, json={"value": 70.0, "reason": REASON})

        response = client.request("DELETE", URL, json={"reason": "short"})

        assert response.status_code == 422
        assert seeded.query(PortfolioEsgOverride).count() == 1

    def test_clear_without_override_is_409(self, client, seeded):
        response = client.request("DELETE", URL, json={"reason": "Nothing to clear here."})
        assert response.status_code == 409

    def test_clear_unknown_account_is_404(self, client, seeded):
        response = client.request("DELETE", "/api/portfolio/9999999999/esg/override", json={"reason": REASON})
        assert response.status_code == 404


class TestGetEsg:
    def test_computed_state(self, client, seeded):
        body = client.get(f"/api/portfolio/{ACCOUNT}/esg").json()
        assert body["hasMetric"] is True
        assert body["source"] == "computed"
        assert body["effectiveValue"] == 64.137484
        assert body["coveragePct"] == 91.48

    def test_known_account_without_metric(self, client, session):
        make_portfolio(session)
        response = client.get(f"/api/portfolio/{ACCOUNT}/esg")
        assert response.status_code == 200
        assert response.json()["hasMetric"] is False
        assert response.json()["source"] == "none"

    def test_unknown_account_is_404(self, client, seeded):
        assert client.get("/api/portfolio/9999999999/esg").status_code == 404
