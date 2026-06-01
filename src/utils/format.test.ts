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
  it('formats a positive amount in USD by default', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56');
  });

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('$0.00');
  });

  it('formats a negative amount', () => {
    expect(formatCurrency(-500.1)).toBe('-$500.10');
  });

  it('respects custom currency', () => {
    const result = formatCurrency(1000, 'EUR');
    // EUR formatting in en-US locale
    expect(result).toContain('1,000.00');
  });

  it('respects custom options overriding decimals', () => {
    const result = formatCurrency(1234.5678, 'USD', {
      minimumFractionDigits: 4,
      maximumFractionDigits: 4,
    });
    expect(result).toContain('1,234.5678');
  });

  it('formats large numbers with commas', () => {
    expect(formatCurrency(1000000)).toBe('$1,000,000.00');
  });
});

describe('formatNumber', () => {
  it('formats a number with 2 decimal places by default', () => {
    expect(formatNumber(1234.5)).toBe('1,234.50');
  });

  it('formats zero', () => {
    expect(formatNumber(0)).toBe('0.00');
  });

  it('formats with custom decimal places', () => {
    expect(formatNumber(1234.5678, 4)).toBe('1,234.5678');
  });

  it('formats with 0 decimal places', () => {
    expect(formatNumber(1234.5, 0)).toBe('1,235');
  });

  it('formats negative numbers', () => {
    expect(formatNumber(-99.9)).toBe('-99.90');
  });
});

describe('formatPercentage', () => {
  it('formats a percentage with 2 decimal places by default', () => {
    expect(formatPercentage(7.5)).toBe('7.50%');
  });

  it('formats zero percent', () => {
    expect(formatPercentage(0)).toBe('0.00%');
  });

  it('formats negative percentage', () => {
    expect(formatPercentage(-3.14)).toBe('-3.14%');
  });

  it('formats with custom decimal places', () => {
    expect(formatPercentage(12.3456, 3)).toBe('12.346%');
  });
});

describe('formatLastUpdated', () => {
  it('formats a Date object', () => {
    const date = new Date(2024, 0, 15, 14, 30); // Jan 15, 2024 2:30 PM
    const result = formatLastUpdated(date);
    expect(result).toContain('January');
    expect(result).toContain('15');
    expect(result).toContain('2024');
  });

  it('formats a valid date string', () => {
    const result = formatLastUpdated('2024-06-20T10:00:00Z');
    expect(result).toContain('2024');
    expect(result).toContain('June');
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
    expect(getGainLossColorClass(0.01)).toBe('text-green-600');
  });

  it('returns red for negative values', () => {
    expect(getGainLossColorClass(-100)).toBe('text-red-600');
    expect(getGainLossColorClass(-0.01)).toBe('text-red-600');
  });

  it('returns gray for zero', () => {
    expect(getGainLossColorClass(0)).toBe('text-gray-600');
  });
});

describe('formatGainLoss', () => {
  it('formats positive gain/loss with + sign', () => {
    const result = formatGainLoss(500, 5.5);
    expect(result.formatted).toContain('+');
    expect(result.formatted).toContain('$500.00');
    expect(result.formatted).toContain('+5.50%');
    expect(result.colorClass).toBe('text-green-600');
  });

  it('formats negative gain/loss', () => {
    const result = formatGainLoss(-200, -3.2);
    expect(result.formatted).toContain('-$200.00');
    expect(result.formatted).toContain('-3.20%');
    expect(result.colorClass).toBe('text-red-600');
  });

  it('formats zero gain/loss with + sign', () => {
    const result = formatGainLoss(0, 0);
    expect(result.formatted).toContain('+');
    expect(result.colorClass).toBe('text-gray-600');
  });

  it('respects custom currency', () => {
    const result = formatGainLoss(100, 2, 'EUR');
    expect(result.formatted).toContain('100.00');
  });
});
