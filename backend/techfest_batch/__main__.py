"""techfest-batch command line.

    python -m techfest_batch seed
    python -m techfest_batch reset
    python -m techfest_batch status
    python -m techfest_batch run --job <id>
    python -m techfest_batch replay --job <id> [--restart] [--json]
    python -m techfest_batch check-retry-safety [--json]
"""
import json
import sys

from techfest_batch.config import settings


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "seed":
        from techfest_batch.seed import seed

        print("seeded:", ", ".join(seed()))
        return 0
    if cmd == "reset":
        from techfest_batch.seed import reset
        from techfest_batch.config import DATA_DIR

        removed = reset()
        for name in ("last_check.json", "last_replay.json"):
            path = DATA_DIR / name
            if path.exists():
                path.unlink()
        print("removed:", ", ".join(removed) or "(nothing)")
        return 0
    if cmd == "status":
        print(json.dumps({"scenario": settings.scenario, "code_revision": settings.code_revision,
                          "database_url": settings.database_url, "fault_injection_enabled": settings.fault_injection_enabled}, indent=2))
        return 0
    if cmd == "run":
        from techfest_batch.worker import main as worker_main

        return worker_main(rest)
    if cmd == "replay":
        from techfest_batch.replay import main as replay_main

        return replay_main(rest)
    if cmd == "check-retry-safety":
        from techfest_batch.check_retry_safety import main as check_main

        return check_main(rest)
    print(f"unknown command: {cmd}", file=sys.stderr)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
