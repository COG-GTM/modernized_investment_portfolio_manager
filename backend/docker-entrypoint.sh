#!/bin/sh
set -e

# Wait for the database to accept connections (Postgres deployments).
# For SQLite (default) this loop is skipped because DATABASE_URL is unset/sqlite.
if [ -n "$DATABASE_URL" ] && [ "${DATABASE_URL#sqlite}" = "$DATABASE_URL" ]; then
  echo "Waiting for database to be ready..."
  python - <<'PY'
import os, time
from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"]
for attempt in range(30):
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database is ready.")
        break
    except Exception as exc:  # noqa: BLE001
        print(f"  db not ready ({attempt + 1}/30): {exc}")
        time.sleep(2)
else:
    raise SystemExit("Database did not become ready in time")
PY
fi

echo "Running database migrations..."
alembic upgrade head

echo "Seeding database (idempotent)..."
python seed_database.py

echo "Starting application: $*"
exec "$@"
