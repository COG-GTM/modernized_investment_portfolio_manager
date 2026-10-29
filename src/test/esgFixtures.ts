import type { EsgAuditEntry, EsgMetric } from '../types/esg';

export const computedMetric: EsgMetric = {
  account_number: '1234567890',
  portfolio_id: 'PF-12345',
  as_of_month: '2026-10',
  unit: 'tCO2e per $M revenue',
  computed_value: 1.313615,
  effective_value: 1.313615,
  source: 'computed',
  coverage_pct: 60.8489,
  computed_at: '2026-10-29T14:44:23',
  override: null,
};

export const overriddenMetric: EsgMetric = {
  ...computedMetric,
  effective_value: 1.1,
  source: 'override',
  override: {
    value: 1.1,
    reason: 'Provider restated MSFT scope 2 for 2026-10',
    changed_by: 'pm_jane',
    changed_at: '2026-10-29T15:02:11',
  },
};

export const auditEntries: EsgAuditEntry[] = [
  {
    id: 2,
    as_of_month: '2026-10',
    action: 'CLEAR',
    old_value: 1.1,
    new_value: null,
    reason: 'Restatement withdrawn by provider',
    changed_by: 'pm_jane',
    changed_at: '2026-10-29T15:10:00',
  },
  {
    id: 1,
    as_of_month: '2026-10',
    action: 'OVERRIDE',
    old_value: null,
    new_value: 1.1,
    reason: 'Provider restated MSFT scope 2 for 2026-10',
    changed_by: 'pm_jane',
    changed_at: '2026-10-29T15:02:11',
  },
];
