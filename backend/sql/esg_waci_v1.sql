-- esg_waci_v1.sql  (RP-47)
-- Weighted Average Carbon Intensity (WACI) per portfolio for one as-of month.
--
--   WACI = SUM( weight_i * (scope1_i + scope2_i) / revenue_i )
--   weight_i = market_value_i / SUM(market_value) over the portfolio's active positions
--   unit: tCO2e per $M revenue
--
-- Rules
--   * Positions are dated snapshots. For each holding the latest snapshot dated inside the
--     as-of month is used; snapshots from other months and holdings opened after month end
--     are ignored, and a holding is never counted twice.
--   * Active positions only (latest snapshot status = 'A'). A holding sold during the month is
--     closed ('C') at month end and therefore excluded, even if an earlier snapshot was active.
--   * Holdings with no staging row for the month, or with NULL / non-positive revenue,
--     are excluded from the sum and counted against coverage_pct.
--   * coverage_pct = covered market value / total market value * 100.
--   * A portfolio whose active market value is zero gets waci_computed = NULL and
--     coverage_pct = 0; there is no division by zero.
--   * Idempotent: rerunning for the same month upserts the computed columns and leaves
--     any manual override (override_* columns) untouched.
--
-- Bind parameters (named, supplied by services/esg_service.py): as_of_month ('YYYY-MM'), computed_at (timestamp)
--
-- SQL Server equivalent: this body would be the stored procedure dbo.usp_compute_portfolio_waci
-- with the INSERT ... ON CONFLICT replaced by MERGE.

WITH month_bounds AS (
    SELECT :as_of_month || '-01'                                   AS month_start,
           date(:as_of_month || '-01', '+1 month', '-1 day')      AS month_end
),
month_snapshots AS (
    SELECT
        p.portfolio_id,
        p.investment_id,
        p.status,
        p.market_value,
        ROW_NUMBER() OVER (PARTITION BY p.portfolio_id, p.investment_id ORDER BY p.date DESC) AS rn
    FROM positions AS p
    CROSS JOIN month_bounds AS mb
    WHERE p.date >= mb.month_start
      AND p.date <= mb.month_end
),
active_positions AS (
    SELECT
        s.portfolio_id,
        s.investment_id,
        CAST(s.market_value AS REAL) AS market_value
    FROM month_snapshots AS s
    WHERE s.rn = 1
      AND s.status = 'A'
      AND s.market_value IS NOT NULL
      AND s.market_value > 0
),
portfolio_totals AS (
    SELECT
        pf.port_id                                   AS portfolio_id,
        COALESCE(SUM(ap.market_value), 0.0)          AS total_market_value
    FROM (SELECT DISTINCT port_id FROM portfolios) AS pf
    LEFT JOIN active_positions AS ap
           ON ap.portfolio_id = pf.port_id
    GROUP BY pf.port_id
),
covered_positions AS (
    SELECT
        ap.portfolio_id,
        ap.market_value,
        (CAST(e.scope1_tco2e AS REAL) + CAST(e.scope2_tco2e AS REAL))
            / CAST(e.revenue_musd AS REAL)           AS carbon_intensity
    FROM active_positions AS ap
    JOIN stg_esg_emissions AS e
      ON e.investment_id = ap.investment_id
     AND e.as_of_month   = :as_of_month
    WHERE e.scope1_tco2e IS NOT NULL
      AND e.scope2_tco2e IS NOT NULL
      AND e.revenue_musd IS NOT NULL
      AND e.revenue_musd > 0
),
aggregated AS (
    SELECT
        t.portfolio_id,
        t.total_market_value,
        COALESCE(SUM(c.market_value), 0.0)                      AS covered_market_value,
        COALESCE(SUM(c.market_value * c.carbon_intensity), 0.0) AS weighted_intensity_sum
    FROM portfolio_totals AS t
    LEFT JOIN covered_positions AS c
           ON c.portfolio_id = t.portfolio_id
    GROUP BY t.portfolio_id, t.total_market_value
)
INSERT INTO portfolio_esg_metrics (
    portfolio_id,
    as_of_month,
    waci_computed,
    coverage_pct,
    total_market_value,
    covered_market_value,
    computed_at
)
SELECT
    a.portfolio_id,
    :as_of_month,
    CASE WHEN a.total_market_value > 0 AND a.covered_market_value > 0
         THEN a.weighted_intensity_sum / a.total_market_value
         ELSE NULL END                                            AS waci_computed,
    CASE WHEN a.total_market_value > 0
         THEN ROUND(a.covered_market_value * 100.0 / a.total_market_value, 4)
         ELSE 0.0 END                                             AS coverage_pct,
    ROUND(a.total_market_value, 2),
    ROUND(a.covered_market_value, 2),
    :computed_at
FROM aggregated AS a
WHERE true  -- required by SQLite so the ON CONFLICT clause is not parsed as a join constraint
ON CONFLICT (portfolio_id, as_of_month) DO UPDATE SET
    waci_computed        = excluded.waci_computed,
    coverage_pct         = excluded.coverage_pct,
    total_market_value   = excluded.total_market_value,
    covered_market_value = excluded.covered_market_value,
    computed_at          = excluded.computed_at;
