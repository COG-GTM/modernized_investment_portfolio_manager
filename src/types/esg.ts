export type EsgSource = 'computed' | 'override' | 'none';

export interface EsgOverride {
  value: number;
  reason: string;
  overriddenBy: string;
  overriddenAt: string;
}

export interface EsgMetric {
  accountNumber: string;
  portfolioId: string;
  hasMetric: boolean;
  asOfMonth: string | null;
  metric: 'WACI';
  unit: string;
  computedValue: number | null;
  effectiveValue: number | null;
  source: EsgSource;
  coveragePct: number | null;
  computedAt: string | null;
  override: EsgOverride | null;
}

export interface EsgOverrideRequest {
  value: number;
  reason: string;
  changedBy?: string;
}

export type EsgOverrideField = 'value' | 'reason';

export type EsgOverrideErrors = Partial<Record<EsgOverrideField, string>>;
