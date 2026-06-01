import { describe, it, expect } from 'vitest';
import {
  formatCurrency,
  formatNumber,
  formatPercentage,
  formatLastUpdated,
  getGainLossColorClass,
  formatGainLoss,
} from './format';

describe('formatCurrency', () => {
  it('formats a positive value as USD by default', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56');
  });

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('$0.00');
  });

  it('formats negative values', () => {
    expect(formatCurrency(-500.1)).toBe('-$500.10');
  });

  it('uses the specified currency', () => {
    const result = formatCurrency(1000, 'EUR');
    expect(result).toContain('1,000.00');
  });

  it('respects custom options', () => {
    const result = formatCurrency(1234.5678, 'USD', { maximumFractionDigits: 4 });
    expect(result).toContain('1,234.5678');
  });

  it('formats large numbers with commas', () => {
    expect(formatCurrency(1000000)).toBe('$1,000,000.00');
  });

  it('pads to two decimal places', () => {
    expect(formatCurrency(5)).toBe('$5.00');
  });
});

describe('formatNumber', () => {
  it('formats a number with default 2 decimals', () => {
    expect(formatNumber(1234.5)).toBe('1,234.50');
  });

  it('formats with 0 decimals', () => {
    expect(formatNumber(1234.5, 0)).toBe('1,235');
  });

  it('formats with custom decimals', () => {
    expect(formatNumber(3.14159, 4)).toBe('3.1416');
  });

  it('formats zero', () => {
    expect(formatNumber(0)).toBe('0.00');
  });

  it('formats negative numbers', () => {
    expect(formatNumber(-42.1)).toBe('-42.10');
  });

  it('formats large numbers with commas', () => {
    expect(formatNumber(9999999.99)).toBe('9,999,999.99');
  });
});

describe('formatPercentage', () => {
  it('formats a percentage with default 2 decimals', () => {
    expect(formatPercentage(12.34)).toBe('12.34%');
  });

  it('formats zero percentage', () => {
    expect(formatPercentage(0)).toBe('0.00%');
  });

  it('formats negative percentage', () => {
    expect(formatPercentage(-5.5)).toBe('-5.50%');
  });

  it('formats with custom decimal places', () => {
    expect(formatPercentage(99.9, 0)).toBe('100%');
  });

  it('formats with more decimal places', () => {
    expect(formatPercentage(3.14159, 4)).toBe('3.1416%');
  });
});

describe('formatLastUpdated', () => {
  it('formats a Date object', () => {
    const date = new Date('2024-01-15T10:30:00Z');
    const result = formatLastUpdated(date);
    expect(result).toContain('2024');
    expect(result).toContain('January');
    expect(result).toContain('15');
  });

  it('formats a valid date string', () => {
    const result = formatLastUpdated('2024-06-20T14:00:00Z');
    expect(result).toContain('2024');
    expect(result).toContain('June');
    expect(result).toContain('20');
  });

  it('falls back to current date for invalid string', () => {
    const result = formatLastUpdated('not-a-date');
    const now = new Date();
    expect(result).toContain(now.getFullYear().toString());
  });
});

describe('getGainLossColorClass', () => {
  it('returns green for positive values', () => {
    expect(getGainLossColorClass(100)).toBe('text-green-600');
  });

  it('returns red for negative values', () => {
    expect(getGainLossColorClass(-50)).toBe('text-red-600');
  });

  it('returns gray for zero', () => {
    expect(getGainLossColorClass(0)).toBe('text-gray-600');
  });

  it('returns green for very small positive values', () => {
    expect(getGainLossColorClass(0.01)).toBe('text-green-600');
  });

  it('returns red for very small negative values', () => {
    expect(getGainLossColorClass(-0.01)).toBe('text-red-600');
  });
});

describe('formatGainLoss', () => {
  it('formats positive gain with plus sign', () => {
    const result = formatGainLoss(500, 10);
    expect(result.formatted).toContain('+');
    expect(result.formatted).toContain('$500.00');
    expect(result.formatted).toContain('10.00%');
    expect(result.colorClass).toBe('text-green-600');
  });

  it('formats negative loss', () => {
    const result = formatGainLoss(-200, -5);
    expect(result.formatted).toContain('-$200.00');
    expect(result.formatted).toContain('-5.00%');
    expect(result.colorClass).toBe('text-red-600');
  });

  it('formats zero gain/loss', () => {
    const result = formatGainLoss(0, 0);
    expect(result.formatted).toContain('$0.00');
    expect(result.formatted).toContain('0.00%');
    expect(result.colorClass).toBe('text-gray-600');
  });

  it('uses custom currency', () => {
    const result = formatGainLoss(100, 2, 'EUR');
    expect(result.formatted).toContain('100.00');
    expect(result.colorClass).toBe('text-green-600');
  });
});
