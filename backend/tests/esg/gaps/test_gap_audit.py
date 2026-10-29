"""Gap hunt (RP-51): audit immutability at the database level, ordering and pagination."""
import json
from datetime import datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from models.esg import EsgOverrideAudit
from services.esg_service import compute_waci, load_esg_feed
from tests.esg.conftest import SAMPLE_FEED, AS_OF, ACCOUNT, PORT_ID

ESG_URL = f"/api/portfolio/{ACCOUNT}/esg"
AUDIT_URL = f"{ESG_URL}/audit"
VALID_REASON = "Provider restated scope 2 emissions"
JSON = {"content-type": "application/json"}


@pytest.fixture
def with_history(client, seeded_db):
    load_esg_feed(seeded_db, SAMPLE_FEED)
    compute_waci(seeded_db, AS_OF)
    for value in (1.0, 2.0, 3.0):
        assert client.put(f"{ESG_URL}/override", json={"value": value, "reason": VALID_REASON}).status_code == 200
    assert client.request("DELETE", f"{ESG_URL}/override", content=json.dumps({"reason": VALID_REASON}), headers=JSON).status_code == 200
    return client


class TestAppendOnlyAtDatabaseLevel:
    def test_update_is_blocked_by_the_database(self, with_history, engine):
        """RP-51: append-only was enforced only by convention in the service; a direct UPDATE succeeded."""
        with pytest.raises(DBAPIError):
            with engine.begin() as con:
                con.execute(text("UPDATE esg_override_audit SET reason = 'tampered'"))

    def test_delete_is_blocked_by_the_database(self, with_history, engine):
        """RP-51: a direct DELETE emptied the trail with no error."""
        with pytest.raises(DBAPIError):
            with engine.begin() as con:
                con.execute(text("DELETE FROM esg_override_audit"))
        with engine.connect() as con:
            assert con.execute(text("SELECT COUNT(*) FROM esg_override_audit")).scalar() == 4

    def test_orm_update_is_blocked_too(self, with_history, seeded_db):
        """RP-51: the same guard must hold for ORM writes, not only raw SQL."""
        row = seeded_db.query(EsgOverrideAudit).first()
        row.reason = "tampered"
        with pytest.raises(DBAPIError):
            seeded_db.commit()
        seeded_db.rollback()


class TestOrderingAndPagination:
    def test_same_timestamp_entries_fall_back_to_id_desc(self, with_history, seeded_db):
        """RP-51: two writes inside the same second must still be newest-first (id is the tiebreaker)."""
        # rows are append-only, so add fresh rows that share the newest existing timestamp exactly
        same = max(row.changed_at for row in seeded_db.query(EsgOverrideAudit).all())
        for value in (10, 11):
            seeded_db.add(EsgOverrideAudit(portfolio_id=PORT_ID, as_of_month=AS_OF, action="OVERRIDE", old_value=None,
                                           new_value=value, reason=VALID_REASON, changed_by="t", changed_at=same))
        seeded_db.commit()
        entries = with_history.get(AUDIT_URL).json()["entries"]
        ids = [e["id"] for e in entries]
        assert ids == sorted(ids, reverse=True)

    def test_limit_is_honoured(self, with_history):
        """RP-51: ?limit=1 returned every row; the endpoint ignored the parameter."""
        body = with_history.get(f"{AUDIT_URL}?limit=1").json()
        assert len(body["entries"]) == 1
        assert body["entries"][0]["action"] == "CLEAR"

    def test_offset_pages_through_history_without_gaps_or_duplicates(self, with_history):
        """RP-51: paging with limit/offset must cover the full history exactly once, newest first."""
        full = [e["id"] for e in with_history.get(f"{AUDIT_URL}?limit=500").json()["entries"]]
        paged = []
        for offset in range(0, len(full), 2):
            paged += [e["id"] for e in with_history.get(f"{AUDIT_URL}?limit=2&offset={offset}").json()["entries"]]
        assert paged == full == sorted(full, reverse=True)

    @pytest.mark.parametrize("query", ["limit=0", "limit=501", "limit=-1", "offset=-1", "limit=abc"])
    def test_out_of_range_paging_parameters_are_422(self, with_history, query):
        """RP-51: unbounded or malformed paging parameters must be rejected, not silently clamped."""
        assert with_history.get(f"{AUDIT_URL}?{query}").status_code == 422

    def test_default_page_size_is_bounded(self, with_history, seeded_db):
        """RP-51: with no limit the endpoint must not return an unbounded result set."""
        for i in range(60):
            seeded_db.add(EsgOverrideAudit(portfolio_id=PORT_ID, as_of_month=AS_OF, action="OVERRIDE", old_value=None,
                                           new_value=i, reason=VALID_REASON, changed_by="t", changed_at=datetime.now()))
        seeded_db.commit()
        assert len(with_history.get(AUDIT_URL).json()["entries"]) == 50
