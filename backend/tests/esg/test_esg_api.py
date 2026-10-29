"""RP-48, RP-50, RP-51 endpoint tests."""
import pytest

from services.esg_service import compute_waci, load_esg_feed
from tests.esg.conftest import SAMPLE_FEED, AS_OF, ACCOUNT

ESG_URL = f"/api/portfolio/{ACCOUNT}/esg"
VALID_REASON = "Provider restated MSFT scope 2 emissions"


@pytest.fixture
def computed(client, seeded_db):
    load_esg_feed(seeded_db, SAMPLE_FEED)
    compute_waci(seeded_db, AS_OF)
    return client


class TestGetEsg:
    def test_returns_computed_metric(self, computed):
        response = computed.get(ESG_URL)
        assert response.status_code == 200
        body = response.json()
        assert body["account_number"] == ACCOUNT
        assert body["portfolio_id"] == "PF-12345"
        assert body["as_of_month"] == AS_OF
        assert body["unit"] == "tCO2e per $M revenue"
        assert body["source"] == "computed"
        assert body["computed_value"] == pytest.approx(1.313615, abs=1e-5)
        assert body["effective_value"] == body["computed_value"]
        assert body["coverage_pct"] == pytest.approx(60.8489, abs=1e-3)
        assert body["override"] is None
        assert body["computed_at"]

    def test_unknown_account_404(self, computed):
        response = computed.get("/api/portfolio/0000000000/esg")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_known_account_without_metric_404(self, client):
        response = client.get(ESG_URL)
        assert response.status_code == 404
        assert "No carbon intensity metric" in response.json()["detail"]


class TestOverride:
    def test_override_applies_and_reports_source(self, computed):
        response = computed.put(f"{ESG_URL}/override", json={"value": 2.25, "reason": VALID_REASON}, headers={"X-User": "pm_jane"})
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "override"
        assert body["effective_value"] == 2.25
        assert body["computed_value"] == pytest.approx(1.313615, abs=1e-5)
        assert body["override"]["reason"] == VALID_REASON
        assert body["override"]["changed_by"] == "pm_jane"

        again = computed.get(ESG_URL).json()
        assert again["source"] == "override" and again["effective_value"] == 2.25

    def test_reason_shorter_than_10_chars_rejected(self, computed):
        response = computed.put(f"{ESG_URL}/override", json={"value": 2.25, "reason": "too short"})
        assert response.status_code == 422
        assert "at least 10 characters" in str(response.json()["detail"])
        assert computed.get(ESG_URL).json()["source"] == "computed"

    def test_missing_reason_rejected(self, computed):
        response = computed.put(f"{ESG_URL}/override", json={"value": 2.25})
        assert response.status_code == 422

    def test_whitespace_only_reason_rejected(self, computed):
        response = computed.put(f"{ESG_URL}/override", json={"value": 2.25, "reason": "               "})
        assert response.status_code == 422
        assert "Reason is mandatory" in response.json()["detail"]

    def test_negative_value_rejected(self, computed):
        response = computed.put(f"{ESG_URL}/override", json={"value": -1, "reason": VALID_REASON})
        assert response.status_code == 422

    def test_zero_value_allowed(self, computed):
        response = computed.put(f"{ESG_URL}/override", json={"value": 0, "reason": VALID_REASON})
        assert response.status_code == 200 and response.json()["effective_value"] == 0

    def test_override_unknown_account_404(self, computed):
        response = computed.put("/api/portfolio/0000000000/esg/override", json={"value": 1, "reason": VALID_REASON})
        assert response.status_code == 404

    def test_override_without_metric_422(self, client):
        response = client.put(f"{ESG_URL}/override", json={"value": 1, "reason": VALID_REASON})
        assert response.status_code == 422
        assert "load the ESG feed" in response.json()["detail"]


class TestClearOverride:
    def test_clear_restores_computed_value(self, computed):
        computed.put(f"{ESG_URL}/override", json={"value": 2.25, "reason": VALID_REASON})
        response = computed.request("DELETE", f"{ESG_URL}/override", json={"reason": "Restatement confirmed by provider"})
        assert response.status_code == 200
        body = response.json()
        assert body["source"] == "computed"
        assert body["effective_value"] == pytest.approx(1.313615, abs=1e-5)
        assert body["override"] is None

    def test_clear_without_override_422(self, computed):
        response = computed.request("DELETE", f"{ESG_URL}/override", json={"reason": "Nothing to clear here"})
        assert response.status_code == 422
        assert "no override to clear" in response.json()["detail"]

    def test_clear_requires_reason(self, computed):
        computed.put(f"{ESG_URL}/override", json={"value": 2.25, "reason": VALID_REASON})
        response = computed.request("DELETE", f"{ESG_URL}/override", json={"reason": "short"})
        assert response.status_code == 422
        assert computed.get(ESG_URL).json()["source"] == "override"


class TestAudit:
    def test_empty_history(self, computed):
        response = computed.get(f"{ESG_URL}/audit")
        assert response.status_code == 200
        assert response.json() == {"account_number": ACCOUNT, "portfolio_id": "PF-12345", "entries": []}

    def test_history_newest_first_and_append_only(self, computed):
        computed.put(f"{ESG_URL}/override", json={"value": 2.0, "reason": "First override for the month"}, headers={"X-User": "pm_a"})
        computed.put(f"{ESG_URL}/override", json={"value": 3.0, "reason": "Second override after review"}, headers={"X-User": "pm_b"})
        computed.request("DELETE", f"{ESG_URL}/override", json={"reason": "Clearing after provider fix"}, headers={"X-User": "pm_c"})

        entries = computed.get(f"{ESG_URL}/audit").json()["entries"]
        assert [e["action"] for e in entries] == ["CLEAR", "OVERRIDE", "OVERRIDE"]
        assert [e["changed_by"] for e in entries] == ["pm_c", "pm_b", "pm_a"]
        assert entries[0]["old_value"] == 3.0 and entries[0]["new_value"] == pytest.approx(1.313615, abs=1e-5)
        assert entries[1]["old_value"] == 2.0 and entries[1]["new_value"] == 3.0
        assert entries[2]["old_value"] == pytest.approx(1.313615, abs=1e-5) and entries[2]["new_value"] == 2.0
        assert all(e["as_of_month"] == AS_OF for e in entries)
        assert all(e["reason"] and e["changed_at"] for e in entries)

    def test_audit_unknown_account_404(self, computed):
        assert computed.get("/api/portfolio/0000000000/esg/audit").status_code == 404
