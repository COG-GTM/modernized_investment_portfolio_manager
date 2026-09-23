"""Fault injector + request-replay tool.

    python -m techfest_batch.replay --job EOD-POST-PORT0002-20240628 [--restart] [--json]

Replays the client's bounded retry sequence against the service for one logical job and emits
a trace (job id, request ids, attempt numbers, timestamps, response codes, code revision per
attempt) as JSON and as a readable table, followed by the completion records now persisted
for that job.
"""
import argparse
import json
import sys
import uuid
from datetime import datetime, timezone

from techfest_batch.client import BatchCompletionClient
from techfest_batch.config import DATA_DIR, settings
from techfest_batch.db import ensure_schema, session_scope
from techfest_batch.server import EphemeralServer
from techfest_batch.service import completions_for_job

LAST_REPLAY_FILE = DATA_DIR / "last_replay.json"


def _persisted(job_id: str) -> list[dict]:
    with session_scope() as session:
        return [c.to_dict() for c in completions_for_job(session, job_id)]


def run_replay(job_id: str, server_url: str | None = None, restart_between_attempts: bool = False) -> dict:
    ensure_schema()
    before = _persisted(job_id)
    trace_attempts: list[dict] = []
    started = datetime.now(timezone.utc).isoformat(timespec="milliseconds")

    def record(rec):
        trace_attempts.append(rec.__dict__.copy())

    if server_url:
        outcome = BatchCompletionClient(server_url).complete(job_id, on_attempt=record)
        servers_used = 1
    elif restart_between_attempts:
        # Simulate a service restart between attempts: new server, same SQLite file.
        servers_used = 0
        outcome = None
        client = BatchCompletionClient("http://127.0.0.1:0")
        attempts = []
        for attempt in range(1, client.max_attempts + 1):
            with EphemeralServer() as server:
                servers_used += 1
                client.base_url = server.base_url
                rec = client.complete_once(job_id, str(uuid.uuid4()), attempt)
                rec.__dict__["server_instance"] = servers_used
                record(rec)
                attempts.append(rec)
            if rec.outcome in ("ok", "error"):
                break
        final = next((a.completion_id for a in attempts if a.outcome == "ok"), None)
        outcome_dict = {
            "job_id": job_id,
            "attempts": [a.__dict__ for a in attempts],
            "final_completion_id": final,
            "exhausted": final is None and all(a.outcome == "timeout" for a in attempts),
        }
    else:
        with EphemeralServer() as server:
            servers_used = 1
            outcome = BatchCompletionClient(server.base_url).complete(job_id, on_attempt=record)

    if outcome is not None:
        outcome_dict = outcome.to_dict()

    after = _persisted(job_id)
    trace = {
        "label": "Synthetic demonstration",
        "tool": "techfest_batch.replay",
        "job_id": job_id,
        "scenario": settings.scenario,
        "fault_injection_enabled": settings.fault_injection_enabled,
        "code_revision": settings.code_revision,
        "client_timeout_s": settings.client_timeout_s,
        "client_max_attempts": settings.client_max_attempts,
        "stall_ms": settings.stall_ms,
        "restart_between_attempts": restart_between_attempts,
        "servers_used": servers_used,
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "attempts": outcome_dict["attempts"],
        "final_completion_id": outcome_dict["final_completion_id"],
        "completions_before": len(before),
        "completions_after": len(after),
        "completions": after,
        "duplicate_detected": len(after) > 1,
    }
    DATA_DIR.mkdir(exist_ok=True)
    LAST_REPLAY_FILE.write_text(json.dumps(trace, indent=2))
    return trace


def format_table(trace: dict) -> str:
    lines = [
        f"Replay trace for job {trace['job_id']}  scenario={trace['scenario']}  "
        f"revision={trace['code_revision'][:12]}  client_timeout={trace['client_timeout_s']}s",
        "",
        f"{'att':>3} {'request_id':<36} {'started_at':<29} {'code':>4} {'outcome':<8} {'completion_id':<36} {'revision':<12}",
    ]
    for a in trace["attempts"]:
        lines.append(
            f"{a['attempt']:>3} {a['request_id']:<36} {a['started_at']:<29} "
            f"{str(a['status_code'] or '-'):>4} {a['outcome']:<8} {a['completion_id'] or '-':<36} "
            f"{(a['code_revision'] or '-')[:12]:<12}"
        )
    lines += ["", f"Persisted completions for {trace['job_id']}: {trace['completions_after']}"]
    for c in trace["completions"]:
        lines.append(
            f"  - {c['completion_id']}  attempt={c['attempt']}  request_id={c['request_id']}  "
            f"completed_at={c['completed_at']}  revision={c['code_revision'][:12]}"
        )
    verdict = "DUPLICATE COMPLETION DETECTED" if trace["duplicate_detected"] else "single completion (invariant holds)"
    lines += ["", f"Result: {verdict}"]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay the client retry sequence for one batch job")
    parser.add_argument("--job", required=True)
    parser.add_argument("--server-url", help="target a running service instead of an ephemeral one")
    parser.add_argument("--restart", action="store_true", help="restart the service between attempts")
    parser.add_argument("--json", action="store_true", help="print JSON only")
    args = parser.parse_args(argv)

    trace = run_replay(args.job, args.server_url, args.restart)
    if args.json:
        print(json.dumps(trace, indent=2))
    else:
        print(format_table(trace))
        print()
        print(json.dumps(trace, indent=2))
    return 1 if trace["duplicate_detected"] else 0


if __name__ == "__main__":
    sys.exit(main())
