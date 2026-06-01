import { describe, it, expect } from 'vitest';
import {
  formatCurrency,
  formatNumber,
  formatPercentage,
  formatLastUpdated,
  getGainLossColorClass,
  formatGainLoss,
} from '../format';

describe('formatCurrency', () => {
  it('formats a positive number as USD by default', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56');
  });

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('$0.00');
  });

  it('formats a negative number', () => {
    expect(formatCurrency(-500.1)).toBe('-$500.10');
  });

  it('rounds to 2 decimal places by default', () => {
    expect(formatCurrency(99.999)).toBe('$100.00');
  });

  it('accepts a different currency code', () => {
    const result = formatCurrency(1000, 'EUR');
    expect(result).toContain('1,000.00');
  });

  it('accepts custom NumberFormat options', () => {
    const result = formatCurrency(1234.5678, 'USD', {
      minimumFractionDigits: 4,
      maximumFractionDigits: 4,
    });
    expect(result).toContain('1,234.5678');
  });

  it('formats large numbers with grouping separators', () => {
    expect(formatCurrency(1000000)).toBe('$1,000,000.00');
  });
});

describe('formatNumber', () => {
  it('formats with 2 decimal places by default', () => {
    expect(formatNumber(1234.5)).toBe('1,234.50');
  });

  it('formats zero', () => {
    expect(formatNumber(0)).toBe('0.00');
  });

  it('formats with 0 decimal places', () => {
    expect(formatNumber(1234.56, 0)).toBe('1,235');
  });

  it('formats with 4 decimal places', () => {
    expect(formatNumber(3.14159, 4)).toBe('3.1416');
  });

  it('formats negative numbers', () => {
    expect(formatNumber(-42.5)).toBe('-42.50');
  });

  it('formats large numbers with grouping', () => {
    expect(formatNumber(9999999.99)).toBe('9,999,999.99');
  });
});

describe('formatPercentage', () => {
  it('appends % to formatted number', () => {
    expect(formatPercentage(12.34)).toBe('12.34%');
  });

  it('formats zero percent', () => {
    expect(formatPercentage(0)).toBe('0.00%');
  });

  it('formats negative percentages', () => {
    expect(formatPercentage(-5.5)).toBe('-5.50%');
  });

  it('respects custom decimal places', () => {
    expect(formatPercentage(99.9999, 3)).toBe('100.000%');
  });

  it('formats with 0 decimals', () => {
    expect(formatPercentage(50.6, 0)).toBe('51%');
  });
});

describe('formatLastUpdated', () => {
  it('formats a Date object', () => {
    const date = new Date('2024-01-15T14:30:00Z');
    const result = formatLastUpdated(date);
    expect(result).toContain('2024');
    expect(result).toContain('January');
    expect(result).toContain('15');
  });

  it('formats a valid date string', () => {
    const result = formatLastUpdated('2024-06-20T10:00:00Z');
    expect(result).toContain('2024');
    expect(result).toContain('June');
    expect(result).toContain('20');
  });

  it('falls back to current date for an invalid string', () => {
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
  it('formats a positive gain with + sign', () => {
    const result = formatGainLoss(500, 10.5);
    expect(result.formatted).toContain('+');
    expect(result.formatted).toContain('$500.00');
    expect(result.formatted).toContain('10.50%');
    expect(result.colorClass).toBe('text-green-600');
  });

  it('formats a negative loss', () => {
    const result = formatGainLoss(-200, -5.25);
    expect(result.formatted).toContain('-$200.00');
    expect(result.formatted).toContain('-5.25%');
    expect(result.colorClass).toBe('text-red-600');
  });

  it('formats zero gain/loss', () => {
    const result = formatGainLoss(0, 0);
    expect(result.formatted).toContain('$0.00');
    expect(result.formatted).toContain('0.00%');
    expect(result.colorClass).toBe('text-gray-600');
  });

  it('uses custom currency', () => {
    const result = formatGainLoss(100, 5, 'EUR');
    expect(result.formatted).toContain('100.00');
    expect(result.colorClass).toBe('text-green-600');
  });
});
