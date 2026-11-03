import type { EsgMetric } from '../types/esg';

export const computedEsg: EsgMetric = {
  accountNumber: '1234567890',
  portfolioId: 'PF-12345',
  hasMetric: true,
  asOfMonth: '2026-11',
  metric: 'WACI',
  unit: 'tCO2e per $M revenue',
  computedValue: 64.137484,
  effectiveValue: 64.137484,
  source: 'computed',
  coveragePct: 91.48,
  computedAt: '2026-11-03T00:20:00',
  override: null,
};

export const overriddenEsg: EsgMetric = {
  ...computedEsg,
  effectiveValue: 70,
  source: 'override',
  override: {
    value: 70,
    reason: 'Provider revenue for TSLA restated; aligned to Q3 filing.',
    overriddenBy: 'SYSTEM',
    overriddenAt: '2026-11-03T00:30:00',
  },
};

export function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}
