"""Gap hunt (RP-50): override validation edge cases the acceptance suite did not pin down."""
import json
from decimal import Decimal

import pytest

from models.esg import EsgOverrideAudit, PortfolioEsgMetrics
from services.esg_service import compute_waci, load_esg_feed, set_override
from tests.esg.conftest import SAMPLE_FEED, AS_OF, ACCOUNT, PORT_ID

ESG_URL = f"/api/portfolio/{ACCOUNT}/esg"
OVERRIDE_URL = f"{ESG_URL}/override"
VALID_REASON = "Provider restated scope 2 emissions"
JSON = {"content-type": "application/json"}


@pytest.fixture
def computed(client, seeded_db):
    load_esg_feed(seeded_db, SAMPLE_FEED)
    compute_waci(seeded_db, AS_OF)
    return client


def _raw_put(client, body: str):
    return client.put(OVERRIDE_URL, content=body, headers=JSON)


class TestNonFiniteValues:
    @pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity", "1e400"])
    def test_non_finite_value_is_a_422_not_a_500(self, computed, literal):
        """RP-50: Python's JSON parser accepts NaN/Infinity tokens and 1e400 overflows to inf; all must be
        rejected as validation errors instead of raising inside the service or the JSON encoder."""
        response = _raw_put(computed, '{"value": %s, "reason": "%s"}' % (literal, VALID_REASON))
        assert response.status_code == 422, response.text

    def test_non_finite_value_does_not_poison_the_metric(self, computed):
        """RP-50/RP-48: before the fix an Infinity override was persisted, after which GET /esg returned 500
        for the account forever (JSON encoder refuses inf). The read path must keep working."""
        _raw_put(computed, '{"value": Infinity, "reason": "%s"}' % VALID_REASON)
        response = computed.get(ESG_URL)
        assert response.status_code == 200, response.text
        assert response.json()["source"] == "computed"

    def test_service_rejects_non_finite_decimal_directly(self, seeded_db):
        """RP-50: the service layer must not rely on the HTTP schema alone (it is also called by scripts)."""
        load_esg_feed(seeded_db, SAMPLE_FEED)
        compute_waci(seeded_db, AS_OF)
        with pytest.raises(Exception) as exc:
            set_override(seeded_db, PORT_ID, Decimal("Infinity"), VALID_REASON, "tester")
        assert "finite" in str(exc.value)
        assert seeded_db.query(EsgOverrideAudit).count() == 0


class TestValueTypeCoercion:
    def test_boolean_is_not_a_valid_value(self, computed):
        """RP-50: {"value": true} was silently coerced to 1.0 and stored as an override."""
        response = computed.put(OVERRIDE_URL, json={"value": True, "reason": VALID_REASON})
        assert response.status_code == 422, response.text

    def test_numeric_string_is_not_a_valid_value(self, computed):
        """RP-50: the API contract is a JSON number; "5" should not be accepted."""
        response = computed.put(OVERRIDE_URL, json={"value": "5", "reason": VALID_REASON})
        assert response.status_code == 422, response.text

    def test_large_but_finite_value_is_accepted_and_round_trips(self, computed):
        """RP-50: a very large finite value is legal and must survive the Numeric round trip."""
        response = computed.put(OVERRIDE_URL, json={"value": 1e12, "reason": VALID_REASON})
        assert response.status_code == 200, response.text
        assert computed.get(ESG_URL).json()["effective_value"] == pytest.approx(1e12)


class TestReasonBoundaries:
    @pytest.mark.parametrize("reason", [" " * 10, "\t\n" * 6, "x" + " " * 20, "123456789"])
    def test_whitespace_padded_or_short_reason_rejected(self, computed, reason):
        """RP-50: 10 characters of whitespace (or 1 real char padded to 10+) must not satisfy the minimum."""
        response = computed.put(OVERRIDE_URL, json={"value": 1.0, "reason": reason})
        assert response.status_code == 422, response.text

    def test_exactly_ten_characters_accepted_and_trimmed_reason_stored(self, computed):
        """RP-50: 10 is the boundary; surrounding whitespace is trimmed before storage."""
        response = computed.put(OVERRIDE_URL, json={"value": 1.0, "reason": "  1234567890  "})
        assert response.status_code == 200, response.text
        assert response.json()["override"]["reason"] == "1234567890"

    def test_failed_validation_writes_no_audit_row(self, computed, seeded_db):
        """RP-50/RP-51: rejected requests leave no trace in the audit trail."""
        computed.put(OVERRIDE_URL, json={"value": 1.0, "reason": " " * 10})
        _raw_put(computed, '{"value": NaN, "reason": "%s"}' % VALID_REASON)
        assert seeded_db.query(EsgOverrideAudit).count() == 0


class TestStateVersusValidation:
    def test_override_before_any_metric_is_a_409_conflict(self, client):
        """RP-50: a well-formed request against a portfolio with no computed month is a state conflict (409),
        not a validation error (422); the UI shows 422s as form errors."""
        response = client.put(OVERRIDE_URL, json={"value": 1.0, "reason": VALID_REASON})
        assert response.status_code == 409, response.text

    def test_clearing_twice_is_a_409_conflict(self, computed):
        """RP-50/RP-51: the second clear must not succeed silently and must not be reported as bad input."""
        computed.put(OVERRIDE_URL, json={"value": 1.0, "reason": VALID_REASON})
        first = computed.request("DELETE", OVERRIDE_URL, content=json.dumps({"reason": VALID_REASON}), headers=JSON)
        assert first.status_code == 200, first.text
        second = computed.request("DELETE", OVERRIDE_URL, content=json.dumps({"reason": VALID_REASON}), headers=JSON)
        assert second.status_code == 409, second.text
        audit = computed.get(f"{ESG_URL}/audit").json()["entries"]
        assert [e["action"] for e in audit] == ["CLEAR", "OVERRIDE"]

    def test_unknown_account_is_404_on_every_route(self, computed):
        """RP-48/RP-50/RP-51: 404 is reserved for unknown accounts on all four routes."""
        base = "/api/portfolio/0000000000/esg"
        assert computed.get(base).status_code == 404
        assert computed.put(f"{base}/override", json={"value": 1.0, "reason": VALID_REASON}).status_code == 404
        assert computed.request("DELETE", f"{base}/override", content=json.dumps({"reason": VALID_REASON}), headers=JSON).status_code == 404
        assert computed.get(f"{base}/audit").status_code == 404


class TestCallerIdentity:
    def test_oversized_x_user_is_rejected(self, computed):
        """RP-51: changed_by is declared String(64); SQLite does not enforce it, so a 500-char header was stored."""
        response = computed.put(OVERRIDE_URL, json={"value": 1.0, "reason": VALID_REASON}, headers={"X-User": "a" * 500})
        assert response.status_code == 422, response.text

    def test_blank_x_user_falls_back_to_default_identity(self, computed):
        """RP-51: a whitespace-only X-User must not be recorded as the actor."""
        response = computed.put(OVERRIDE_URL, json={"value": 1.0, "reason": VALID_REASON}, headers={"X-User": "   "})
        assert response.status_code == 200, response.text
        assert response.json()["override"]["changed_by"].strip() != ""
        audit = computed.get(f"{ESG_URL}/audit").json()["entries"]
        assert audit[0]["changed_by"].strip() != ""

    @pytest.mark.xfail(strict=True, reason="Open: X-User is a caller-supplied header, not an authenticated identity; "
                                            "any client can write the audit trail as any user (RP-51).")
    def test_caller_cannot_impersonate_another_user(self, computed):
        """RP-51: the actor recorded in the audit trail should come from an authenticated principal.
        The existing portfolio endpoint has no account-level rules either (validation bypassed), so there is
        nothing to inherit; this is documented as an open finding."""
        response = computed.put(OVERRIDE_URL, json={"value": 1.0, "reason": VALID_REASON}, headers={"X-User": "someone_else"})
        assert response.status_code in (401, 403)


class TestConcurrentOverrides:
    def test_stale_writer_does_not_break_audit_chain(self, engine, seeded_db):
        """RP-50/RP-51: two managers load the metric at the same time; the second commit must either fail or
        record the first writer's value as old_value so the audit chain (old_value[n+1] == new_value[n]) holds."""
        from sqlalchemy.orm import sessionmaker
        load_esg_feed(seeded_db, SAMPLE_FEED)
        compute_waci(seeded_db, AS_OF)
        Session = sessionmaker(bind=engine)
        a, b = Session(), Session()
        a.query(PortfolioEsgMetrics).filter_by(portfolio_id=PORT_ID).one()
        b.query(PortfolioEsgMetrics).filter_by(portfolio_id=PORT_ID).one()
        set_override(a, PORT_ID, Decimal("2"), VALID_REASON, "manager_a")
        set_override(b, PORT_ID, Decimal("3"), VALID_REASON, "manager_b")
        rows = seeded_db.query(EsgOverrideAudit).order_by(EsgOverrideAudit.id).all()
        assert len(rows) == 2
        assert rows[1].old_value == rows[0].new_value
