"""
Load a nightly position file into the positions table.

Usage:
    python load_positions.py                # latest file under inbound/positions/
    python load_positions.py <path/to.csv>  # a specific file
"""
import sys
from pathlib import Path

from models.database import SessionLocal
from services.position_loader import find_latest_position_file, load_position_file


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else find_latest_position_file()
    if path is None or not path.exists():
        print("No position file found to load.")
        return 1

    session = SessionLocal()
    try:
        result = load_position_file(path, session)
    finally:
        session.close()

    print(f"Loaded {result.loaded} position rows from {result.file} ({result.skipped} skipped)")
    for error in result.errors:
        print(f"  ! {error}")
    return 0 if result.ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
