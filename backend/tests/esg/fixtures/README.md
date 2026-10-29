# ESG feed fixtures (Jira epic RP-45)

Fixture files mirror the inbound bucket layout `esg/<YYYY-MM>/esg_emissions_<YYYY-MM>.csv`
that the RP-46 loader reads from `backend/inbound/esg/`. Columns:
`as_of_month, investment_id, scope1_tco2e, scope2_tco2e, revenue_musd`.

Seeded positions (see `conftest.py::seeded_portfolios`, all dated 2026-10-31, status `A`):

| Portfolio | Account    | Investment | Market value (USD) |
|-----------|------------|------------|--------------------|
| PORT0001  | 1234567890 | INV0000001 | 60,000             |
| PORT0001  | 1234567890 | INV0000002 | 30,000             |
| PORT0001  | 1234567890 | INV0000003 | 10,000             |
| PORT0002  | 2222222222 | INV0000004 | 0                  |
| PORT0003  | 3333333333 | (none)     |                    |

## esg/2026-10/esg_emissions_2026-10.csv (clean feed, 5 rows, 0 rejects)

| investment_id | scope1 | scope2 | revenue ($M) | intensity = (s1+s2)/rev |
|---------------|--------|--------|--------------|-------------------------|
| INV0000001    | 120.0  | 80.0   | 50.0         | 200 / 50 = 4.0          |
| INV0000002    | 30.0   | 15.0   | 15.0         | 45 / 15 = 3.0           |
| INV0000003    | 10.0   | 5.0    | (blank)      | excluded, no revenue    |
| INV0000004    | 500.0  | 250.0  | 25.0         | 750 / 25 = 30.0         |
| INV0000009    | 7.5    | 2.5    | 10.0         | not held by anyone      |

### Hand-computed WACI for PORT0001, 2026-10

Weight = position market value / total active market value of the portfolio
(100,000). Holdings without revenue are excluded from the sum and counted
against coverage.

```
weight(INV0000001) = 60,000 / 100,000 = 0.60   contribution 0.60 * 4.0 = 2.40
weight(INV0000002) = 30,000 / 100,000 = 0.30   contribution 0.30 * 3.0 = 0.90
weight(INV0000003) = 10,000 / 100,000 = 0.10   excluded (revenue missing)

WACI         = 2.40 + 0.90 = 3.30 tCO2e per $M revenue
coverage_pct = (60,000 + 30,000) / 100,000 = 90.0 %
```

`EXPECTED_WACI_MAIN = 3.3`, `EXPECTED_COVERAGE_MAIN = 90.0` in `conftest.py`.

If the implementation instead normalises weights over *covered* market value
only (an open question in `docs/specs/esg-test-matrix.md`), the value would be
`(60,000 * 4.0 + 30,000 * 3.0) / 90,000 = 3.6667`. The suite asserts 3.3; change
the constant in one place if product decides otherwise.

PORT0002 has a single position with zero market value: total market value 0,
so the procedure must not divide by zero. Expected: no exception, metric row
with `computed_value` NULL (or 0) and `coverage_pct` 0.

### Position sold mid-month (RP-47)

`test_rp47_procedure.py` adds a closed (`status='C'`) position INV0000004 dated
2026-10-15 with a stale market value of 40,000 to PORT0001. If it were wrongly
included, WACI would become (240,000 + 90,000 + 1,200,000) / 140,000 = 10.93.
Expected WACI stays 3.3 and coverage stays 90 %.

## esg/2026-10/esg_emissions_2026-10_with_rejects.csv (2 good rows, 5 rejects)

| row | problem                                | expected outcome           |
|-----|----------------------------------------|----------------------------|
| 3   | negative scope1 (`-5.0`)               | rejects table, reason text |
| 4   | non-numeric scope1 (`abc`)             | rejects table              |
| 5   | empty investment_id                    | rejects table              |
| 6   | invalid month `2026-13`                | rejects table              |
| 7   | negative revenue (`-3.0`)              | rejects table              |

## esg/2026-10/esg_emissions_2026-10_short_rows.csv

Row 2 has only three columns. Expected: that row is rejected, the first row loads.

## esg/2026-11/esg_emissions_2026-11.csv

Next month's feed, used for "override applies to the current as-of month only".

```
INV0000001: 200 / 50 = 4.00  weight 0.60  -> 2.400
INV0000002:  30 / 15 = 2.00  weight 0.30  -> 0.600
INV0000003:  15 / 20 = 0.75  weight 0.10  -> 0.075
WACI 2026-11 = 3.075, coverage 100 %
```
