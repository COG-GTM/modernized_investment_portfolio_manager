"""Load a monthly ESG emissions file from the inbound bucket folder and compute WACI (RP-46, RP-47).

Run from the backend/ directory:
    python -m scripts.load_esg_feed inbound/esg/2026-10/esg_emissions_2026-10.csv
    python -m scripts.load_esg_feed inbound/esg/2026-10/esg_emissions_2026-10.csv --no-compute
"""
import argparse
import sys

from models.database import SessionLocal
from services.esg_service import EsgFeedError, compute_waci, load_esg_feed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Load an ESG emissions CSV into staging and compute WACI.")
    parser.add_argument("path", help="Path to the feed file, e.g. inbound/esg/2026-10/esg_emissions_2026-10.csv")
    parser.add_argument("--no-compute", action="store_true", help="Only stage the file; skip the WACI calculation")
    args = parser.parse_args(argv)

    db = SessionLocal()
    try:
        result = load_esg_feed(db, args.path)
        if result.skipped:
            print(f"File already loaded as batch {result.batch_id}; no rows added.")
        else:
            print(f"Batch {result.batch_id}: {result.loaded_rows} rows staged, {result.rejected_rows} rejected.")
            for reject in result.rejects:
                print(f"  reject row {reject['row_no']}: {reject['reason']}")
        if not args.no_compute:
            for month in result.as_of_months:
                computed = compute_waci(db, month)
                print(f"WACI computed for {computed.as_of_month}: {computed.portfolios} portfolio(s).")
        return 0
    except EsgFeedError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
