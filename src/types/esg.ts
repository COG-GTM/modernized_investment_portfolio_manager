export type EsgSource = 'computed' | 'override' | 'none';

export interface EsgOverrideDetails {
  value: number;
  reason: string;
  changed_by: string;
  changed_at: string;
}

export interface EsgMetric {
  account_number: string;
  portfolio_id: string;
  /** False for a known account that has no computed month yet (the API then returns 200 with null fields). */
  has_metric?: boolean;
  as_of_month: string;
  unit: string;
  computed_value: number | null;
  effective_value: number | null;
  source: EsgSource;
  coverage_pct: number;
  computed_at: string;
  override: EsgOverrideDetails | null;
}

export type EsgAuditAction = 'OVERRIDE' | 'CLEAR';

export interface EsgAuditEntry {
  id: number;
  as_of_month: string;
  action: EsgAuditAction;
  old_value: number | null;
  new_value: number | null;
  reason: string;
  changed_by: string;
  changed_at: string;
}

export interface EsgAuditResponse {
  account_number: string;
  portfolio_id: string;
  entries: EsgAuditEntry[];
}

export const ESG_MIN_REASON_LENGTH = 10;
