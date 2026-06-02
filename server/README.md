# Portfolio DB Layer (Drizzle / TypeScript)

TypeScript data layer for the Modernized Investment Portfolio Manager, migrated
from the Python SQLAlchemy + Alembic backend (`backend/`). It uses
[Drizzle ORM](https://orm.drizzle.team/) with the node-postgres (`pg`) driver,
mirroring the Drizzle setup in `COG-GTM/Cloudscape-Dashboard`.

> Scope: schema, migrations, DB connection, data-access/service layer, and
> seed + verify scripts only. The Express API routes + validation are migrated
> separately. The service/repository functions here are exported for that layer
> to consume.

## Layout

| Path | Purpose |
| --- | --- |
| `src/db/schema.ts` | Drizzle schema for `portfolios`, `positions`, `transactions`, `history` (ported from `backend/models/*.py`). |
| `src/db/index.ts` | `pg` Pool + Drizzle connection (reads `DATABASE_URL`). |
| `src/db/migrate.ts` | Applies migrations from `drizzle/`. |
| `drizzle/` | Generated SQL migrations (Drizzle Kit) reproducing the Alembic schema. |
| `src/models/*.ts` | Model logic ported from the SQLAlchemy classes (validation, calculations, `to_dict`, audit records). |
| `src/services/portfolioService.ts` | `PortfolioService` ported from `backend/services/portfolio_service.py`. |
| `src/services/portfolioRepository.ts` | Importable data-access helpers for the routes layer. |
| `src/seed.ts` | Seed script ported from `backend/seed_database.py`. |
| `src/verify.ts` | Persistence verification ported from `backend/verify_persistence.py`. |
| `src/server.ts` | Minimal Express scaffold to run/exercise the DB layer in isolation. |

## Configuration

Set `DATABASE_URL` (PostgreSQL). The Python backend defaulted to a local SQLite
file; this layer targets PostgreSQL to match Cloudscape-Dashboard. A local
default of `postgresql://postgres:postgres@localhost:5432/portfolio` is used when
unset. See `.env.example`.

## Usage

```bash
npm install
npm run build          # tsc

export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/portfolio
npm run db:generate    # regenerate migrations from schema (optional)
npm run db:migrate     # apply migrations
npm run db:seed        # seed sample portfolio
npm run db:verify      # verify persistence

npm run dev            # run the minimal Express scaffold
```

## Notes on the port

- **Foreign keys:** the SQLAlchemy models declared FKs referencing
  `portfolios.port_id` while `portfolios` has a composite PK
  (`port_id`, `account_no`). SQLite tolerated this; PostgreSQL requires the
  referenced column to be unique, so a `UNIQUE(port_id)` constraint is added to
  preserve the relationship.
- **`history.time` length:** the SQLAlchemy model used `String(8)` but the
  applied Alembic migration created `varchar(6)`. The schema follows the
  migration (the resulting schema), and audit timestamps are generated as
  `HHMMSS`.
- **Decimals:** monetary/quantity columns use `numeric`, and arithmetic uses
  `decimal.js` to preserve precision (never floating point), matching the Python
  `Decimal` usage.
