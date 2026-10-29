# ESG carbon intensity feed: acceptance test matrix (Jira epic RP-45)

The suite was written from the acceptance criteria before the implementation
landed. On `main` today every backend test skips (the `services.esg_service`
module and the `/esg` routes do not exist) and every frontend test fails with
a message naming the story. Run it against the implementation PR with:

```bash
# backend, one story at a time or the whole suite
cd backend && source .venv/bin/activate
python -m pytest tests/esg -m rp46        # ... rp47, rp48, rp49, rp50, rp51
python -m pytest tests/esg -m esg

# frontend
npm test                                  # vitest run
```

Fixture CSVs and the hand-computed WACI live in `backend/tests/esg/fixtures/README.md`.

## Contract the suite assumes

These are the names the stories gave us plus the minimum the tests had to pin
down. Anything not listed here is left to the implementer.

| Area | Assumed contract |
|------|------------------|
| Loader | `services.esg_service.load_feed(path) -> LoadResult`; `LoadResult` exposes a batch id (`batch_id` or `load_batch_id`) and row counts (`rows_loaded` / `rows_rejected`, aliases accepted). Missing file raises. |
| Staging | `stg_esg_emissions(as_of_month, investment_id, scope1_tco2e, scope2_tco2e, revenue_musd NULLable, load_batch_id)`; rejects in `stg_esg_emissions_rejects` with a `*reason*` and `*batch*` column. |
| Procedure | `services.esg_service.compute_waci(as_of_month) -> list` of dict/objects with `portfolio_id`, `as_of_month`, `computed_value` (alias `waci`), `coverage_pct`, `computed_at`; persisted in `portfolio_esg_metrics` with those columns; SQL in `backend/sql/*.sql` (name contains `waci` or `esg`). |
| Weights | weight = position market value / total market value of **all** active positions for the month (uncovered holdings dilute WACI, see open question 1). |
| Database | all DB access through `models.database.SessionLocal`; the suite rebinds it to a throw-away SQLite file built with `alembic upgrade head`, so new tables need migrations. |
| API | `GET /api/portfolio/{account_number}/esg` -> `{as_of_month, computed_value, effective_value, source: "computed" or "override", coverage_pct, override: null or {value, reason, overridden_by, overridden_at}}`; 404 unknown account; 200 with nulls for a known account without a metric. |
| Override | `PUT /api/portfolio/{account_number}/esg/override` body `{value, reason}`; validation errors as 400 or 422 with the field name in the body; acting user from `X-User` header; `DELETE` on the same path with body `{reason}` clears the override. |
| Audit | `esg_override_audit` with who / when / old value / new value / reason / as_of_month (column aliases accepted, see `conftest.normalise_audit`); `GET /api/portfolio/{account_number}/esg/audit` returns a list (or `{items: [...]}`) newest first. |
| UI | `CarbonIntensityCard` (`data-testid="carbon-intensity-card"`, `data-testid="override-indicator"`, buttons named Override / History, `role="status"` while loading, empty-state text matching `/no carbon intensity/i`) and `OverrideModal` (`role="dialog"`, fields labelled Value / Reason, button "Save override", inline errors with `role="alert"`, `serverError` prop). |

## Matrix

| Story | Acceptance criterion | Test id | Edge case covered |
|-------|----------------------|---------|-------------------|
| RP-46 | Loader callable as `load_feed(path)` returning `LoadResult` | test_rp46_01 | contract only |
| RP-46 | CSV copied into `stg_esg_emissions` with a load batch id | test_rp46_02 | all rows share one batch id |
| RP-46 | Staged values equal CSV values | test_rp46_03 | blank revenue stored as NULL, not 0 |
| RP-46 | Re-running the same file does not duplicate rows | test_rp46_04 | per-investment uniqueness |
| RP-46 | Re-run does not duplicate rejects | test_rp46_05 | rejects idempotent too |
| RP-46 | Malformed rows go to rejects with a reason | test_rp46_06 | good rows in same file still load |
| RP-46 | Negative emissions rejected | test_rp46_07 | reason text mentions the problem |
| RP-46 | Negative revenue rejected | test_rp46_08 | |
| RP-46 | Invalid month / blank investment id rejected | test_rp46_09 | `2026-13`, empty id |
| RP-46 | Short row rejected, loader continues | test_rp46_10 | row with 3 of 5 columns |
| RP-46 | Missing file is an error | test_rp46_11 | no silent empty load |
| RP-46 | Each run gets its own batch id | test_rp46_12 | second month file |
| RP-47 | Calculation is a versioned SQL script under `backend/sql/` | test_rp47_01, test_rp47_02 | script upserts on (portfolio, month) |
| RP-47 | WACI = sum(weight * (s1+s2)/revenue) | test_rp47_03 | hand-computed 3.3 |
| RP-47 | Results keyed by (portfolio, as_of_month) with computed_at, coverage_pct | test_rp47_04 | |
| RP-47 | Missing revenue excluded and counted against coverage | test_rp47_05 | coverage 90 % |
| RP-47 | Holding absent from feed treated as missing data | test_rp47_06 | not treated as zero emissions |
| RP-47 | Coverage 100 % when all holdings covered | test_rp47_07 | second month, WACI 3.075 |
| RP-47 | Zero total market value does not divide by zero | test_rp47_08 | NULL/0 value, 0 coverage |
| RP-47 | Position sold mid-month excluded | test_rp47_09 | closed row with stale market value |
| RP-47 | Only positions of the as-of month used | test_rp47_10 | prior-month row ignored |
| RP-47 | Rerun idempotent | test_rp47_11 | one row, newer computed_at |
| RP-47 | Rerun reflects restated staging data | test_rp47_12 | value replaced (4.5) |
| RP-47 | Portfolio without positions | test_rp47_13 | NULL or no row, no error |
| RP-47 | Month with no staged data | test_rp47_14 | nothing fabricated |
| RP-48 | GET returns as_of_month, computed_value, effective_value, source, coverage_pct | test_rp48_01 | |
| RP-48 | Override details only when present | test_rp48_02, test_rp48_07 | computed_value survives override |
| RP-48 | 404 unknown account | test_rp48_03 | body names account/portfolio |
| RP-48 | Known account with no metric | test_rp48_04 | 200 with nulls, not 404 |
| RP-48 | Most recent month returned | test_rp48_05 | two months stored |
| RP-48 | NULL value passthrough | test_rp48_06 | zero market value portfolio |
| RP-48 | Malformed account number | test_rp48_08 | never 500 |
| RP-48 | Identifier consistency | test_rp48_09 | optional fields |
| RP-49 | Payload carries value, month, coverage | test_rp49_01 | optional `unit` field |
| RP-49 | Empty state distinguishable from error | test_rp49_02 | |
| RP-49 | Indicator driven by `source` | test_rp49_03 | |
| RP-49 | Effective value with unit | RP-49-01 (vitest) | |
| RP-49 | As-of month shown | RP-49-02 | |
| RP-49 | Coverage shown | RP-49-03 | |
| RP-49 | Indicator when value is an override | RP-49-04, RP-49-05, RP-49-06 | computed value still visible |
| RP-49 | Empty state when no metric | RP-49-07, RP-49-08 | null payload and null fields |
| RP-49 | Loading state | RP-49-09 | |
| RP-49 | Override / History entry points | RP-49-10, RP-49-11, RP-49-12 | no Override in empty state |
| RP-49 | Zero value is not the empty state | RP-49-13 | |
| RP-50 | PUT applies override | test_rp50_01, test_rp50_02 | PUT response carries new state |
| RP-50 | Reason mandatory | test_rp50_03 | |
| RP-50 | Reason minimum 10 characters | test_rp50_04, test_rp50_05, test_rp50_15 | 9 chars rejected, 10 accepted, padding rejected |
| RP-50 | Value non-negative | test_rp50_06, test_rp50_07, test_rp50_08 | -0.01 rejected, 0 accepted, non-numeric |
| RP-50 | Applies to current as-of month only | test_rp50_09, test_rp50_10 | new month not overridden; other month not targetable |
| RP-50 | Second override replaces first | test_rp50_11 | |
| RP-50 | Unknown account / no computed month | test_rp50_12, test_rp50_13 | |
| RP-50 | Validation errors returned | test_rp50_14 | body names both failing fields |
| RP-50 | Modal fields and dialog role | RP-50-01, RP-50-02, RP-50-03 | shows month |
| RP-50 | Client-side validation | RP-50-05 .. RP-50-10, RP-50-16 | boundaries mirror the API |
| RP-50 | Server error shown | RP-50-11 | |
| RP-50 | Context, cancel, escape, double submit | RP-50-12 .. RP-50-15 | |
| RP-51 | Audit table columns | test_rp51_01 | alias tolerant |
| RP-51 | Override writes audit row | test_rp51_02, test_rp51_12 | old value is computed value |
| RP-51 | Chained overrides | test_rp51_03 | old value is previous override |
| RP-51 | Clearing writes a new row | test_rp51_04 | new value null, computed restored |
| RP-51 | Append-only | test_rp51_05, test_rp51_06 | rows unchanged; UPDATE/DELETE blocked in DB |
| RP-51 | GET audit newest first | test_rp51_07 | includes clear row |
| RP-51 | Empty history / unknown account | test_rp51_08, test_rp51_09 | |
| RP-51 | Failed override, clear with nothing active | test_rp51_10, test_rp51_11 | no misleading rows |
| RP-51 | Dashboard history view entry point | RP-49-11 (vitest) | |

RP-52 is the suite itself; the five scenarios it names map to test_rp46_04
(duplicate file), test_rp47_05 (missing revenue), test_rp47_08 (zero market
value), test_rp47_09 (position sold mid-month) and test_rp46_07 (negative
emissions rejected).

## Business-logic questions the stories leave open

1. **Weight denominator.** Is the weight the share of total portfolio market
   value (uncovered holdings dilute WACI; the suite assumes this, expected 3.3)
   or the share of covered market value only (expected 3.6667)? PCAF-style
   reporting usually rescales to covered value and publishes coverage alongside.
2. **Override expiry.** When a new month is computed, does an override on the
   previous month expire (suite assumes yes: the new month is `computed`), carry
   forward, or require explicit re-confirmation?
3. **Position sold mid-month.** With one position row per date, is "active for
   the as-of month" the latest row in the month, the month-end row, or any row
   with status `A`? What if a position has an `A` row on the 1st and a `C` row
   on the 20th? The suite only covers a single closed row.
4. **Currency of revenue.** `revenue_musd` is in USD millions while positions
   carry a `currency` column. Are non-USD position market values converted to
   USD before weighting, and at which rate and date?
5. **Coverage threshold.** Should a WACI with coverage below some threshold
   (for example 50 %) be hidden, flagged, or shown as-is on the dashboard?
6. **Missing revenue vs malformed row.** Is a blank revenue a legitimate data
   gap (staged with NULL, excluded from WACI; suite assumes this) or a malformed
   row that belongs in the rejects table?
7. **Zero revenue.** A revenue of exactly 0 with positive emissions makes
   intensity infinite. Reject at load, exclude at compute, or cap?
8. **Zero market value portfolios.** Should the procedure write a row with a
   NULL value or write nothing? The suite accepts both, but the API and UI
   behaviour differ (empty state vs "0").
9. **Account to portfolio mapping.** An account can own several portfolios
   (`portfolios` has a composite key). Does the API return the WACI of one
   portfolio, an aggregate, or a list?
10. **Who is the overriding user.** The application has no authentication. The
    suite assumes an `X-User` header; production will need a real identity.
11. **Clearing an override.** The stories say clearing writes an audit row but do
    not define the endpoint or whether a reason is mandatory for clearing. The
    suite assumes `DELETE .../esg/override` with a reason.
12. **Append-only enforcement.** Application convention or database triggers?
    test_rp51_06 expects the database to reject UPDATE and DELETE.
13. **Restated feeds.** If the provider re-sends a corrected file for a month
    already loaded, is that a duplicate (ignored) or a restatement (replace)?
    The suite only requires that an identical file is not duplicated.
14. **Feed arrival without positions.** Emissions for an investment nobody holds
    (INV0000009) are staged but unused. Should they be reported anywhere?
15. **Scope 3.** The feed carries scope 1 and 2 only. Will scope 3 arrive later
    and should the schema anticipate it?
16. **Precision and rounding.** How many decimals are stored and displayed for
    WACI and coverage, and is rounding done in SQL or in the UI?
