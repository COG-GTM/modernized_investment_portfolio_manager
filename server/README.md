# Portfolio Manager — Express/TypeScript server

Express + TypeScript backend for the Modernized Investment Portfolio Manager,
migrated from the Python/FastAPI service under `backend/`. The structure mirrors
the `packages/server` reference in `COG-GTM/Cloudscape-Dashboard`.

## Routes

All routes are served under `/api` on port `8000`, matching the frontend client
in `src/services/api.ts`:

- `GET /api/portfolio/:accountNumber` — portfolio summary + holdings (mock data)
- `GET /api/transactions/:accountNumber` — transaction history (placeholder)
- `GET /api/accounts/:accountNumber/validate` — account number validation
- `GET /healthz` — health check

Account validation is intentionally bypassed in the portfolio/transactions
routes (IDOR behavior), faithfully replicating the original FastAPI service.

## Layout

```
server/
  src/
    index.ts                  # entrypoint: loads env, starts the server
    app.ts                    # builds the Express app (mounts routers)
    routes/                   # Express routers (portfolio, accounts)
    validation/portfolio.ts   # validation logic ported from backend/validation
    models/portfolio.ts       # Zod schemas + inferred types (ported Pydantic)
    services/portfolioService.ts  # data-access seam (in-memory mock for now)
```

The database/ORM layer (SQLAlchemy → Drizzle) is owned by a separate migration.
`services/portfolioService.ts` defines a `PortfolioRepository` interface so a
Drizzle-backed implementation can be dropped in without touching the routes.

## Scripts

```bash
npm install        # from the server/ directory
npm run dev        # tsx watch (hot reload)
npm run build      # tsc -> dist/
npm start          # node dist/index.js
npm run lint       # eslint
```

Configure the port via `.env` (see `.env.example`); defaults to `8000`.
