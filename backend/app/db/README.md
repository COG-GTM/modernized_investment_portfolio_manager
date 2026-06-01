# Database Schema — DB2/VSAM to PostgreSQL Migration

This directory contains SQLAlchemy ORM models migrated from the legacy COBOL
Investment Portfolio Management System
([COG-GTM/COBOL-Legacy-Benchmark-Suite](https://github.com/COG-GTM/COBOL-Legacy-Benchmark-Suite)).

## Source-to-Target Mapping

### DB2 Tables (`src/database/db2/`)

| DB2 Source File | DB2 Table | SQLAlchemy Model | PostgreSQL Table | Primary Key |
|---|---|---|---|---|
| `db2-definitions.sql` | `PORTFOLIO_MASTER` | `PortfolioMaster` | `portfolio_master` | `portfolio_id` |
| `db2-definitions.sql` | `INVESTMENT_POSITIONS` | `InvestmentPosition` | `investment_positions` | `(portfolio_id, investment_id, position_date)` |
| `db2-definitions.sql` | `TRANSACTION_HISTORY` | `TransactionHistory` | `transaction_history` | `transaction_id` |
| `POSHIST.sql` | `POSHIST` | `PositionHistory` | `position_history` | `(account_no, portfolio_id, trans_date, trans_time)` |
| `ERRLOG.sql` | `ERRLOG` | `ErrorLog` | `error_log` | `(error_timestamp, program_id)` |
| `RTNCODES.sql` | `RTNCODES` | `ReturnCode` | `return_codes` | `(timestamp, program_id)` |

### VSAM Replacement Tables (`src/database/vsam/`)

| VSAM Source | VSAM File | SQLAlchemy Model | PostgreSQL Table | Primary Key |
|---|---|---|---|---|
| `vsam-definitions.txt` | `PORTMSTR` (KSDS) | `PositionMaster` | `position_master` | `(portfolio_id, security_id)` |
| `vsam-definitions.txt` | `TRANHIST` (KSDS) | `TransactionFile` | `transaction_file` | `(transaction_date, transaction_time, portfolio_id, sequence_no)` |

### DB2 Non-Table Objects (Not Migrated as Tables)

| Source File | Object | Notes |
|---|---|---|
| `PORTPLAN.sql` | DB2 Plan Bindings | Replaced by SQLAlchemy session/connection management |
| `db2-definitions.sql` | `ACTIVE_PORTFOLIOS` view | Can be recreated as a SQLAlchemy query or DB view |
| `db2-definitions.sql` | `CURRENT_POSITIONS` view | Can be recreated as a SQLAlchemy query or DB view |

## Type Mapping

| DB2 Type | PostgreSQL Type | SQLAlchemy Type | Notes |
|---|---|---|---|
| `CHAR(n)` | `VARCHAR(n)` | `String(n)` | PostgreSQL `VARCHAR` is used; no padding |
| `VARCHAR(n)` | `VARCHAR(n)` | `String(n)` | Direct mapping |
| `DECIMAL(p,s)` | `NUMERIC(p,s)` | `Numeric(p,s)` | Exact decimal — never Float |
| `INTEGER` | `INTEGER` | `Integer` | Direct mapping |
| `DATE` | `DATE` | `Date` | Direct mapping |
| `TIME` | `TIME` | `Time` | Direct mapping |
| `TIMESTAMP` | `TIMESTAMP` | `DateTime` | Direct mapping |

## Index Mapping

| Original Index | Table | Columns | PostgreSQL Index |
|---|---|---|---|
| `IDX_PORT_MASTER_CLIENT` | `portfolio_master` | `(client_id, status)` | `idx_port_master_client` |
| `IDX_POSITIONS_DATE` | `investment_positions` | `(position_date, portfolio_id)` | `idx_positions_date` |
| `IDX_TRANS_HIST_PORT` | `transaction_history` | `(portfolio_id, transaction_date)` | `idx_trans_hist_port` |
| `IDX_TRANS_HIST_DATE` | `transaction_history` | `(transaction_date, portfolio_id)` | `idx_trans_hist_date` |
| `POSHIST_IX1` | `position_history` | `(security_id, trans_date)` | `poshist_ix1` |
| `POSHIST_IX2` | `position_history` | `(process_date, program_id)` | `poshist_ix2` |
| `ERRLOG_IX1` | `error_log` | `(process_date, error_severity DESC)` | `errlog_ix1` |
| `RTNCODES_PRG_IDX` | `return_codes` | `(program_id, timestamp)` | `rtncodes_prg_idx` |
| `RTNCODES_STS_IDX` | `return_codes` | `(status_code, timestamp)` | `rtncodes_sts_idx` |

## Foreign Keys

| Child Table | Column | Parent Table | Parent Column |
|---|---|---|---|
| `investment_positions` | `portfolio_id` | `portfolio_master` | `portfolio_id` |
| `transaction_history` | `portfolio_id` | `portfolio_master` | `portfolio_id` |

## Directory Layout

```
backend/app/db/
├── __init__.py              # Exports Base, engine, SessionLocal, get_db
├── database.py              # Engine creation, session factory, env-var config
├── README.md                # This file
└── models/
    ├── __init__.py           # Exports all 8 model classes
    ├── portfolio_master.py   # DB2 PORTFOLIO_MASTER
    ├── investment_positions.py # DB2 INVESTMENT_POSITIONS
    ├── transaction_history.py  # DB2 TRANSACTION_HISTORY
    ├── position_history.py   # DB2 POSHIST
    ├── error_log.py          # DB2 ERRLOG
    ├── return_codes.py       # DB2 RTNCODES
    ├── position_master.py    # VSAM PORTMSTR/POSHIST replacement
    └── transaction_file.py   # VSAM TRANHIST replacement
```

## Configuration

Set the `DATABASE_URL` environment variable to point at your PostgreSQL instance:

```bash
export DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/portfolio_db"
```

If unset, the system falls back to a local SQLite database (`portfolio.db`) for
development convenience.

## Running Migrations

```bash
cd backend
python -m alembic upgrade head
```

To roll back the DB2/VSAM tables only:

```bash
python -m alembic downgrade 40a256798f94
```

## Design Decisions

1. **Numeric over Float** — All financial columns use `Numeric`/`Decimal` to
   prevent floating-point rounding errors, matching the DB2 `DECIMAL` type.

2. **Composite primary keys preserved** — Every composite key from the original
   DB2/VSAM definitions is faithfully reproduced.

3. **VSAM KSDS patterns** — The `position_master` and `transaction_file` tables
   use composite primary keys that mirror the VSAM key structures, supporting
   the same access patterns (key-sequenced lookups and sequential date-range
   scans via indexed columns).

4. **Partitioning deferred** — The DB2 `POSHIST` table was range-partitioned by
   `TRANS_DATE`. The SQLAlchemy model defines the logical schema; PostgreSQL
   native partitioning can be applied as a follow-up migration when needed.

5. **Separate model base** — The new models use their own `Base` instance
   (`app.db.database.Base`) to avoid collisions with the pre-existing legacy
   models in `backend/models/`.
