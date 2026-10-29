/**
 * Shared helpers for the ESG dashboard acceptance tests (Jira RP-49, RP-50, RP-51).
 *
 * The components under test do not exist on main yet. They are loaded with a
 * dynamic import so that a missing module fails each test with a message that
 * names the story, instead of failing the whole file at collection time.
 */
import type { ComponentType } from 'react';

export interface EsgOverride {
  value: number;
  reason: string;
  overridden_by: string;
  overridden_at: string;
}

export interface EsgMetric {
  as_of_month: string;
  computed_value: number | null;
  effective_value: number | null;
  source: 'computed' | 'override' | null;
  coverage_pct: number | null;
  override: EsgOverride | null;
}

export const COMPUTED_METRIC: EsgMetric = {
  as_of_month: '2026-10',
  computed_value: 3.3,
  effective_value: 3.3,
  source: 'computed',
  coverage_pct: 90,
  override: null,
};

export const OVERRIDDEN_METRIC: EsgMetric = {
  as_of_month: '2026-10',
  computed_value: 3.3,
  effective_value: 2.75,
  source: 'override',
  coverage_pct: 90,
  override: {
    value: 2.75,
    reason: 'Issuer restated scope 2 figures',
    overridden_by: 'pm_jane',
    overridden_at: '2026-11-02T09:15:00Z',
  },
};

export const EMPTY_METRIC: EsgMetric = {
  as_of_month: '2026-10',
  computed_value: null,
  effective_value: null,
  source: null,
  coverage_pct: null,
  override: null,
};

export const AS_OF_MONTH_PATTERN = /2026-10|Oct(ober)?\s+2026/i;
export const UNIT_PATTERN = /tCO2e\s*(\/|per)\s*\$?M/i;
export const OVERRIDE_INDICATOR_PATTERN = /overrid/i;
export const EMPTY_STATE_PATTERN = /no carbon intensity|carbon intensity (is )?not available|no esg data/i;

const COMPONENT_PATHS: Record<string, string> = {
  CarbonIntensityCard: '@/components/CarbonIntensityCard',
  OverrideModal: '@/components/OverrideModal',
};

export async function loadComponent<P = any>(name: string, story: string): Promise<ComponentType<P>> {
  const modulePath = COMPONENT_PATHS[name];
  try {
    const mod = await import(/* @vite-ignore */ modulePath);
    const component = mod.default ?? mod[name];
    if (!component) {
      throw new Error(`module has no default export or named export '${name}'`);
    }
    return component as ComponentType<P>;
  } catch (error) {
    throw new Error(
      `${story}: src/components/${name}.tsx is not implemented yet (${(error as Error).message})`
    );
  }
}
