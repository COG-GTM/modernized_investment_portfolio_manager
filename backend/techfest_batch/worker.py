"""Worker/CLI: run a batch job and report its completion through the client.

    python -m techfest_batch.worker --job EOD-POST-PORT0001-20240628 [--server-url http://localhost:8000]

Without --server-url an ephemeral in-process server is started against the configured database.
"""
import argparse
import json
import sys

from techfest_batch.client import BatchCompletionClient
from techfest_batch.config import settings
from techfest_batch.db import ensure_schema, session_scope
from techfest_batch.seed import seed
from techfest_batch.server import EphemeralServer
from techfest_batch.service import list_jobs


def run_job(job_id: str, server_url: str | None = None) -> dict:
    if server_url:
        client = BatchCompletionClient(server_url)
        return client.complete(job_id).to_dict()
    with EphemeralServer() as server:
        client = BatchCompletionClient(server.base_url)
        return client.complete(job_id).to_dict()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a batch job and post its completion")
    parser.add_argument("--job", help="logical job id; omit to run every pending seeded job")
    parser.add_argument("--server-url", help="use a running service instead of an ephemeral one")
    parser.add_argument("--seed", action="store_true", help="seed the synthetic jobs first")
    args = parser.parse_args(argv)

    ensure_schema()
    if args.seed:
        seed()

    if args.job:
        job_ids = [args.job]
    else:
        with session_scope() as session:
            job_ids = [j.job_id for j in list_jobs(session) if j.status != "COMPLETED"]

    results = []
    for job_id in job_ids:
        result = run_job(job_id, args.server_url)
        results.append(result)
        status = "completed" if result["final_completion_id"] else "FAILED"
        print(f"{job_id}: {status} after {len(result['attempts'])} attempt(s)  [scenario={settings.scenario}]")
    print(json.dumps(results, indent=2))
    return 0 if all(r["final_completion_id"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
