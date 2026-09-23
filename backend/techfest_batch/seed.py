from decimal import Decimal

from techfest_batch.config import FAULT_PRE_ACK_STALL
from techfest_batch.db import ensure_schema, session_scope
from techfest_batch.service import delete_job, ensure_job

RUN_DATE = "20240628"

# Synthetic end-of-day posting jobs. PORT0002 carries the injected pre-ack stall.
SEED_JOBS = [
    ("EOD-POST-PORT0001-20240628", "PORT0001", 14, Decimal("125430.50"), None),
    ("EOD-POST-PORT0002-20240628", "PORT0002", 9, Decimal("88210.00"), FAULT_PRE_ACK_STALL),
    ("EOD-POST-PORT0003-20240628", "PORT0003", 21, Decimal("310775.25"), None),
    ("EOD-POST-PORT0004-20240628", "PORT0004", 3, Decimal("4200.00"), None),
]

STALL_JOB_ID = SEED_JOBS[1][0]


def seed() -> list[str]:
    ensure_schema()
    with session_scope() as session:
        for job_id, portfolio_id, count, total, fault in SEED_JOBS:
            ensure_job(session, job_id, RUN_DATE, portfolio_id, count, total, fault)
    return [j[0] for j in SEED_JOBS]


def reset(include_check_jobs: bool = True) -> list[str]:
    """Remove only this scenario's jobs and completions; nothing else in the database is touched."""
    ensure_schema()
    removed: list[str] = []
    with session_scope() as session:
        from techfest_batch.service import list_jobs

        for job in list_jobs(session):
            if job.job_id.startswith("EOD-POST-") or (include_check_jobs and job.job_id.startswith("CHECK-")):
                removed.append(job.job_id)
                delete_job(session, job.job_id)
    return removed
