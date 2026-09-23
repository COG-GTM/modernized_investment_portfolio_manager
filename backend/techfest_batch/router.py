import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from techfest_batch import service
from techfest_batch.config import DATA_DIR, settings
from techfest_batch.db import session_scope

router = APIRouter(prefix="/batch", tags=["batch"])

LAST_CHECK_FILE = DATA_DIR / "last_check.json"
LAST_REPLAY_FILE = DATA_DIR / "last_replay.json"


class CompleteRequest(BaseModel):
    request_id: str = Field(min_length=1, max_length=36)
    attempt: int = Field(ge=1, le=10)


class CreateJobRequest(BaseModel):
    job_id: str = Field(min_length=1, max_length=64)
    run_date: str = Field(min_length=8, max_length=8)
    portfolio_id: str = Field(min_length=8, max_length=8)
    transaction_count: int = 0
    total_amount: str = "0.00"
    fault_injection: str | None = None


def _read_json(path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


@router.get("/status")
def batch_status():
    return {
        "label": "Synthetic demonstration",
        "scenario": settings.scenario,
        "fault_injection_enabled": settings.fault_injection_enabled,
        "code_revision": settings.code_revision,
        "stall_ms": settings.stall_ms,
        "client_timeout_s": settings.client_timeout_s,
        "client_max_attempts": settings.client_max_attempts,
        "last_check": _read_json(LAST_CHECK_FILE),
        "last_replay": _read_json(LAST_REPLAY_FILE),
    }


@router.get("/jobs")
def list_jobs():
    with session_scope() as session:
        jobs = []
        for job in service.list_jobs(session):
            data = job.to_dict()
            data["completions"] = [c.to_dict() for c in service.completions_for_job(session, job.job_id)]
            data["completion_count"] = len(data["completions"])
            jobs.append(data)
        return {"jobs": jobs}


@router.post("/jobs", status_code=201)
def create_job(body: CreateJobRequest):
    with session_scope() as session:
        job = service.ensure_job(
            session,
            body.job_id,
            body.run_date,
            body.portfolio_id,
            body.transaction_count,
            body.total_amount,
            body.fault_injection,
        )
        return job.to_dict()


@router.get("/jobs/{job_id}/completions")
def job_completions(job_id: str):
    with session_scope() as session:
        completions = service.completions_for_job(session, job_id)
        return {"job_id": job_id, "completions": [c.to_dict() for c in completions]}


@router.post("/jobs/{job_id}/complete")
def complete_job(job_id: str, body: CompleteRequest):
    with session_scope() as session:
        try:
            result = service.complete_job(session, job_id, body.request_id, body.attempt)
        except service.JobNotFound:
            raise HTTPException(status_code=404, detail=f"Unknown batch job {job_id}")
        return result.to_dict()


@router.post("/replay")
def run_replay_endpoint(body: dict):
    from techfest_batch.replay import run_replay

    job_id = body.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")
    trace = run_replay(job_id, restart_between_attempts=bool(body.get("restart", False)))
    return trace


@router.post("/check-retry-safety")
def run_check_endpoint():
    from techfest_batch.check_retry_safety import run_check

    return run_check()
