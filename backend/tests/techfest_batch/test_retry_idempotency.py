"""Regression coverage for the completion invariant: one persisted completion per logical job,
across client retries (fresh request id per attempt), concurrent requests and a service restart.

Every test here runs against a SQLite file through SQLAlchemy; the "restart" cases dispose the
engine and reopen the same file so no in-process state can satisfy the dedup.
"""
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from techfest_batch import db, service
from techfest_batch.config import FAULT_PRE_ACK_STALL, settings
from techfest_batch.models import BatchCompletion
from techfest_batch.server import create_app

JOB = "EOD-POST-PORT0002-20240628"
OTHER_JOB = "EOD-POST-PORT0001-20240628"


@pytest.fixture
def batch_db(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'batch.db'}"
    monkeypatch.setattr(settings, "database_url", url)
    db.ensure_schema(url)
    yield url
    db.dispose_all()


@pytest.fixture
def api(batch_db):
    return TestClient(create_app())


def _seed(job_id=JOB, fault=None):
    with db.session_scope() as session:
        service.ensure_job(session, job_id, "20240628", job_id.split("-")[2], 3, Decimal("100.00"), fault)


def _rows(job_id=JOB):
    with db.session_scope() as session:
        return session.query(BatchCompletion).filter_by(job_id=job_id).order_by(BatchCompletion.attempt).all()


def _restart_storage(url):
    """Simulate a service restart: drop every engine/connection and reopen the same SQLite file."""
    db.dispose_all()
    db.ensure_schema(url)


class TestRetryIdempotency:
    def test_retry_with_fresh_request_id_returns_same_completion(self, batch_db):
        _seed()
        with db.session_scope() as session:
            first = service.complete_job(session, JOB, str(uuid.uuid4()), 1)
        with db.session_scope() as session:
            second = service.complete_job(session, JOB, str(uuid.uuid4()), 2)
        assert first.deduplicated is False
        assert second.deduplicated is True
        assert second.completion.completion_id == first.completion.completion_id
        rows = _rows()
        assert len(rows) == 1
        assert rows[0].completion_id == first.completion.completion_id

    def test_timeout_retry_via_api_with_fault_injector_armed(self, api, monkeypatch):
        monkeypatch.setattr(settings, "scenario", "broken")
        monkeypatch.setattr(settings, "stall_ms", 50)
        _seed(fault=FAULT_PRE_ACK_STALL)
        # Client contract: fresh request id per attempt; attempt 1 timed out client-side.
        r1 = api.post(f"/batch/jobs/{JOB}/complete", json={"request_id": str(uuid.uuid4()), "attempt": 1})
        r2 = api.post(f"/batch/jobs/{JOB}/complete", json={"request_id": str(uuid.uuid4()), "attempt": 2})
        assert r1.status_code == 200 and r2.status_code == 200
        assert r2.json()["completion_id"] == r1.json()["completion_id"]
        assert r2.json()["deduplicated"] is True
        assert len(_rows()) == 1

    def test_bounded_retry_burst_yields_single_completion(self, api):
        _seed()
        ids = set()
        for attempt in range(1, settings.client_max_attempts + 1):
            r = api.post(f"/batch/jobs/{JOB}/complete", json={"request_id": str(uuid.uuid4()), "attempt": attempt})
            assert r.status_code == 200
            ids.add(r.json()["completion_id"])
        assert len(ids) == 1
        assert len(_rows()) == 1

    def test_concurrent_requests_yield_single_completion(self, api):
        _seed()
        workers = 8
        barrier = threading.Barrier(workers)

        def fire(attempt):
            barrier.wait()
            return api.post(f"/batch/jobs/{JOB}/complete", json={"request_id": str(uuid.uuid4()), "attempt": attempt})

        with ThreadPoolExecutor(max_workers=workers) as pool:
            responses = list(pool.map(fire, range(1, workers + 1)))
        assert all(r.status_code == 200 for r in responses), [r.text for r in responses]
        ids = {r.json()["completion_id"] for r in responses}
        assert len(ids) == 1
        assert sum(1 for r in responses if r.json()["deduplicated"] is False) == 1
        rows = _rows()
        assert len(rows) == 1
        assert rows[0].completion_id == ids.pop()

    def test_concurrent_service_calls_on_separate_sessions(self, batch_db):
        _seed()
        workers = 6
        barrier = threading.Barrier(workers)
        results = []

        def run(attempt):
            barrier.wait()
            with db.session_scope() as session:
                results.append(service.complete_job(session, JOB, str(uuid.uuid4()), attempt))

        threads = [threading.Thread(target=run, args=(i,)) for i in range(1, workers + 1)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(results) == workers
        assert len({r.completion.completion_id for r in results}) == 1
        assert len(_rows()) == 1

    def test_dedup_survives_restart_with_fresh_request_id(self, batch_db):
        _seed()
        with db.session_scope() as session:
            first = service.complete_job(session, JOB, str(uuid.uuid4()), 1)
        _restart_storage(batch_db)
        with db.session_scope() as session:
            second = service.complete_job(session, JOB, str(uuid.uuid4()), 2)
        assert second.deduplicated is True
        assert second.completion.completion_id == first.completion.completion_id
        assert len(_rows()) == 1

    def test_dedup_survives_restart_via_new_app_instance(self, batch_db):
        _seed()
        request_id = str(uuid.uuid4())
        first = TestClient(create_app()).post(f"/batch/jobs/{JOB}/complete", json={"request_id": request_id, "attempt": 1})
        _restart_storage(batch_db)
        second = TestClient(create_app()).post(
            f"/batch/jobs/{JOB}/complete", json={"request_id": str(uuid.uuid4()), "attempt": 2}
        )
        assert first.status_code == 200 and second.status_code == 200
        assert second.json()["completion_id"] == first.json()["completion_id"]
        assert len(_rows()) == 1

    def test_storage_rejects_second_completion_for_same_job(self, batch_db):
        """The guarantee lives in the schema, not only in service code."""
        from sqlalchemy.exc import IntegrityError

        _seed()
        with db.session_scope() as session:
            service.complete_job(session, JOB, str(uuid.uuid4()), 1)
        with db.session_scope() as session:
            session.add(BatchCompletion(completion_id=str(uuid.uuid4()), job_id=JOB, attempt=2,
                                        request_id=str(uuid.uuid4()), code_revision="x"))
            with pytest.raises(IntegrityError):
                session.commit()
        assert len(_rows()) == 1

    def test_distinct_jobs_still_get_their_own_completion(self, api):
        _seed(JOB)
        _seed(OTHER_JOB)
        ra = api.post(f"/batch/jobs/{JOB}/complete", json={"request_id": str(uuid.uuid4()), "attempt": 1})
        rb = api.post(f"/batch/jobs/{OTHER_JOB}/complete", json={"request_id": str(uuid.uuid4()), "attempt": 1})
        assert ra.json()["completion_id"] != rb.json()["completion_id"]
        assert rb.json()["deduplicated"] is False
        assert len(_rows(JOB)) == 1 and len(_rows(OTHER_JOB)) == 1
