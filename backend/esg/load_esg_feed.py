"""CLI: load the monthly ESG feed into staging.

Run from backend/:
    python -m esg.load_esg_feed --file inbound/esg/2026-10/esg_emissions_2026-10.csv
    python -m esg.load_esg_feed --all

Exit code 0 when every file is loaded (or already loaded), 1 when any file fails.
"""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from esg.loader import INBOUND_ROOT_ENV, EsgFeedError, LoadResult, discover_feeds, load_feed
from models.database import SessionLocal


def _report(result: LoadResult) -> None:
    print(result.summary())
    if result.skipped:
        return
    if result.status != "C":
        print(f"ERROR: {result.file_path} failed ({result.failure_reason}); staging left unchanged", file=sys.stderr)
    elif result.rejected_count:
        print(
            f"WARNING: {result.file_path}: {result.rejected_count} row(s) rejected, see esg_load_rejects for batch {result.batch_id}",
            file=sys.stderr,
        )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m esg.load_esg_feed", description=__doc__.splitlines()[0])
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--file", help="path to one esg/<YYYY-MM>/esg_emissions_<YYYY-MM>.csv file")
    target.add_argument("--all", action="store_true", help="load every file under <inbound-root>/esg/*/ not yet loaded")
    parser.add_argument(
        "--inbound-root",
        default=None,
        help=f"inbound bucket root (default: ${INBOUND_ROOT_ENV} or ./inbound)",
    )
    args = parser.parse_args(argv)

    paths = [args.file] if args.file else discover_feeds(args.inbound_root)
    if not paths:
        print("No ESG feed files found", file=sys.stderr)
        return 0

    exit_code = 0
    session = SessionLocal()
    try:
        for path in paths:
            try:
                result = load_feed(session, path, args.inbound_root)
            except (EsgFeedError, FileNotFoundError) as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                exit_code = 1
                continue
            _report(result)
            exit_code = max(exit_code, result.exit_code)
    finally:
        session.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
