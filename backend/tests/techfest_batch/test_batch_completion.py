"""Unit + integration coverage for the batch-completion service (single-attempt cases, distinct jobs)."""
import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from techfest_batch import db, service
from techfest_batch.config import settings
from techfest_batch.models import BatchCompletion
from techfest_batch.server import create_app


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


def _job(session, suffix="0001", fault=None):
    return service.ensure_job(session, f"EOD-POST-PORT{suffix}-20240628", "20240628", f"PORT{suffix}",
                              3, Decimal("100.00"), fault)


class TestServiceUnit:
    def test_completion_is_persisted_with_attempt_and_revision(self, batch_db):
        with db.session_scope() as session:
            job = _job(session)
            result = service.complete_job(session, job.job_id, str(uuid.uuid4()), 1)
            assert result.deduplicated is False
            assert result.completion.attempt == 1
            assert result.completion.code_revision == settings.code_revision
        with db.session_scope() as session:
            rows = session.query(BatchCompletion).filter_by(job_id=job.job_id).all()
            assert len(rows) == 1
            assert session.get(type(job), job.job_id).status == "COMPLETED"

    def test_unknown_job_raises(self, batch_db):
        with db.session_scope() as session:
            with pytest.raises(service.JobNotFound):
                service.complete_job(session, "EOD-POST-NOPE-20240628", str(uuid.uuid4()), 1)

    def test_distinct_jobs_get_distinct_completions(self, batch_db):
        with db.session_scope() as session:
            a, b = _job(session, "0001"), _job(session, "0003")
            ra = service.complete_job(session, a.job_id, str(uuid.uuid4()), 1)
            rb = service.complete_job(session, b.job_id, str(uuid.uuid4()), 1)
            assert ra.completion.completion_id != rb.completion.completion_id
            assert len(service.completions_for_job(session, a.job_id)) == 1
            assert len(service.completions_for_job(session, b.job_id)) == 1

    def test_total_amount_is_fixed_decimal_string(self, batch_db):
        with db.session_scope() as session:
            job = service.ensure_job(session, "EOD-POST-PORT0009-20240628", "20240628", "PORT0009", 1, Decimal("10.5"))
            assert job.total_amount == "10.50"
            assert isinstance(job.total_amount, str)

    def test_no_stall_in_baseline_scenario(self, batch_db, monkeypatch):
        monkeypatch.setattr(settings, "scenario", "baseline")
        with db.session_scope() as session:
            job = _job(session, "0002", fault="PRE_ACK_STALL")
            assert service.pre_ack_stall_ms(job, 1) == 0


class TestApiIntegration:
    def test_complete_endpoint_returns_completion(self, api):
        api.post("/batch/jobs", json={"job_id": "EOD-POST-PORT0001-20240628", "run_date": "20240628",
                                       "portfolio_id": "PORT0001"})
        resp = api.post("/batch/jobs/EOD-POST-PORT0001-20240628/complete",
                        json={"request_id": str(uuid.uuid4()), "attempt": 1})
        assert resp.status_code == 200
        body = resp.json()
        assert body["job_id"] == "EOD-POST-PORT0001-20240628"
        assert body["attempt"] == 1
        assert body["deduplicated"] is False

        listed = api.get("/batch/jobs").json()["jobs"]
        assert listed[0]["completion_count"] == 1

    def test_complete_unknown_job_is_404(self, api):
        resp = api.post("/batch/jobs/EOD-POST-MISSING-20240628/complete",
                        json={"request_id": str(uuid.uuid4()), "attempt": 1})
        assert resp.status_code == 404

    def test_status_reports_scenario_and_revision(self, api):
        body = api.get("/batch/status").json()
        assert body["scenario"] in ("baseline", "broken")
        assert body["code_revision"]
        assert body["label"] == "Synthetic demonstration"

    def test_two_jobs_two_completions(self, api):
        for pid in ("PORT0003", "PORT0004"):
            api.post("/batch/jobs", json={"job_id": f"EOD-POST-{pid}-20240628", "run_date": "20240628",
                                           "portfolio_id": pid})
            r = api.post(f"/batch/jobs/EOD-POST-{pid}-20240628/complete",
                         json={"request_id": str(uuid.uuid4()), "attempt": 1})
            assert r.status_code == 200
        jobs = api.get("/batch/jobs").json()["jobs"]
        assert [j["completion_count"] for j in jobs] == [1, 1]
