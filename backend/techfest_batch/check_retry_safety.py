"""Independent retry-safety validation check.

    python -m techfest_batch check-retry-safety

Exercises the batch-completion service through HTTP against the persistent SQLite store:
distinct jobs, same-request replay, client timeout + bounded retry (with the pre-ack fault
injector armed on the probe job), and a resend across a service restart. Exit code 1 on failure.
This check is intentionally NOT part of the default test command.
"""
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from techfest_batch.client import BatchCompletionClient
from techfest_batch.config import DATA_DIR, FAULT_PRE_ACK_STALL, settings
from techfest_batch.db import ensure_schema, session_scope
from techfest_batch.server import EphemeralServer
from techfest_batch.service import completions_for_job, delete_job, ensure_job, list_jobs

LAST_CHECK_FILE = DATA_DIR / "last_check.json"
RUN_DATE = "20240628"


def _cleanup_check_jobs() -> None:
    with session_scope() as session:
        for job in list_jobs(session):
            if job.job_id.startswith("CHECK-"):
                delete_job(session, job.job_id)


def _new_job(prefix: str, portfolio: str, fault: str | None = None) -> str:
    job_id = f"CHECK-{prefix}-{uuid.uuid4().hex[:8]}"
    with session_scope() as session:
        ensure_job(session, job_id, RUN_DATE, portfolio, 5, Decimal("1000.00"), fault)
    return job_id


def _count(job_id: str) -> list[dict]:
    with session_scope() as session:
        return [c.to_dict() for c in completions_for_job(session, job_id)]


def probe_distinct_jobs(server: EphemeralServer) -> dict:
    client = BatchCompletionClient(server.base_url)
    a, b = _new_job("DISTINCT-A", "PORT0011"), _new_job("DISTINCT-B", "PORT0012")
    ra, rb = client.complete(a), client.complete(b)
    ca, cb = _count(a), _count(b)
    passed = len(ca) == 1 and len(cb) == 1 and ra.final_completion_id != rb.final_completion_id
    return {
        "name": "distinct_jobs_get_distinct_completions",
        "passed": passed,
        "details": {"jobs": [a, b], "completions": [len(ca), len(cb)]},
    }


def probe_same_request_replay(server: EphemeralServer) -> dict:
    client = BatchCompletionClient(server.base_url)
    job = _new_job("REPLAY", "PORT0013")
    request_id = str(uuid.uuid4())
    first = client.complete_once(job, request_id, 1)
    second = client.complete_once(job, request_id, 1)
    records = _count(job)
    passed = (
        first.outcome == "ok"
        and second.outcome == "ok"
        and first.completion_id == second.completion_id
        and len(records) == 1
    )
    return {
        "name": "same_request_id_replay_is_idempotent",
        "passed": passed,
        "details": {"job": job, "completion_ids": [first.completion_id, second.completion_id], "records": len(records)},
    }


def probe_timeout_retry(server: EphemeralServer) -> dict:
    """Client times out on attempt 1 (injected pre-ack stall) and retries with a fresh request id."""
    client = BatchCompletionClient(server.base_url)
    job = _new_job("TIMEOUT-RETRY", "PORT0014", FAULT_PRE_ACK_STALL)
    outcome = client.complete(job)
    # Let a stalled first attempt finish server-side before counting.
    time.sleep(settings.stall_ms / 1000.0 + 0.3)
    records = _count(job)
    ids = {r["completion_id"] for r in records}
    passed = len(records) == 1 and outcome.final_completion_id in ids
    return {
        "name": "timeout_then_retry_yields_single_completion",
        "passed": passed,
        "details": {
            "job": job,
            "attempts": [a.__dict__ for a in outcome.attempts],
            "final_completion_id": outcome.final_completion_id,
            "persisted_completions": records,
        },
    }


def probe_restart_resend(server: EphemeralServer) -> tuple[dict, EphemeralServer]:
    """Complete a job, restart the service (same SQLite file), resend the identical request."""
    client = BatchCompletionClient(server.base_url)
    job = _new_job("RESTART", "PORT0015")
    request_id = str(uuid.uuid4())
    first = client.complete_once(job, request_id, 1)
    server.stop()
    server = EphemeralServer().start()
    client.base_url = server.base_url
    second = client.complete_once(job, request_id, 1)
    records = _count(job)
    passed = first.completion_id is not None and first.completion_id == second.completion_id and len(records) == 1
    return (
        {
            "name": "resend_across_service_restart_is_deduplicated",
            "passed": passed,
            "details": {"job": job, "completion_ids": [first.completion_id, second.completion_id], "records": len(records)},
        },
        server,
    )


def run_check() -> dict:
    ensure_schema()
    _cleanup_check_jobs()
    started = datetime.now(timezone.utc)
    probes: list[dict] = []
    server = EphemeralServer().start()
    try:
        probes.append(probe_distinct_jobs(server))
        probes.append(probe_same_request_replay(server))
        probes.append(probe_timeout_retry(server))
        probe, server = probe_restart_resend(server)
        probes.append(probe)
    finally:
        server.stop()

    result = {
        "label": "Synthetic demonstration",
        "check": "techfest-batch check-retry-safety",
        "result": "PASS" if all(p["passed"] for p in probes) else "FAIL",
        "scenario": settings.scenario,
        "fault_injection_enabled": settings.fault_injection_enabled,
        "code_revision": settings.code_revision,
        "started_at": started.isoformat(timespec="milliseconds"),
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "probes": probes,
    }
    DATA_DIR.mkdir(exist_ok=True)
    LAST_CHECK_FILE.write_text(json.dumps(result, indent=2))
    return result


def format_result(result: dict) -> str:
    lines = [
        f"{result['check']}  scenario={result['scenario']}  revision={result['code_revision'][:12]}",
        "",
    ]
    for p in result["probes"]:
        lines.append(f"  [{'PASS' if p['passed'] else 'FAIL'}] {p['name']}")
        if not p["passed"]:
            lines.append("         " + json.dumps(p["details"], default=str)[:600])
    lines += ["", f"RESULT: {result['result']}"]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    as_json = "--json" in (argv or sys.argv[1:])
    result = run_check()
    print(json.dumps(result, indent=2) if as_json else format_result(result))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
