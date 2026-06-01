import { describe, it, expect } from 'vitest';
import {
  formatCurrency,
  formatNumber,
  formatPercentage,
  formatLastUpdated,
  getGainLossColorClass,
  formatGainLoss,
} from '../../utils/format';

describe('formatCurrency', () => {
  it('formats positive USD values with 2 decimal places', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56');
  });

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('$0.00');
  });

  it('formats negative values', () => {
    expect(formatCurrency(-500.99)).toBe('-$500.99');
  });

  it('formats large numbers with commas', () => {
    expect(formatCurrency(1234567.89)).toBe('$1,234,567.89');
  });

  it('rounds to 2 decimal places', () => {
    expect(formatCurrency(10.999)).toBe('$11.00');
  });

  it('accepts a different currency', () => {
    const result = formatCurrency(100, 'EUR');
    expect(result).toContain('100.00');
  });

  it('accepts custom options', () => {
    const result = formatCurrency(1000, 'USD', { minimumFractionDigits: 0 });
    expect(result).toContain('1,000');
  });
});

describe('formatNumber', () => {
  it('formats with default 2 decimal places', () => {
    expect(formatNumber(1234.5)).toBe('1,234.50');
  });

  it('formats with 0 decimal places', () => {
    expect(formatNumber(1234.5, 0)).toBe('1,235');
  });

  it('formats with 4 decimal places', () => {
    expect(formatNumber(1.23456, 4)).toBe('1.2346');
  });

  it('formats zero', () => {
    expect(formatNumber(0)).toBe('0.00');
  });

  it('formats negative numbers', () => {
    expect(formatNumber(-42.1, 2)).toBe('-42.10');
  });

  it('formats large numbers with commas', () => {
    expect(formatNumber(1000000, 0)).toBe('1,000,000');
  });
});

describe('formatPercentage', () => {
  it('formats with default 2 decimal places and % sign', () => {
    expect(formatPercentage(7.5)).toBe('7.50%');
  });

  it('formats zero', () => {
    expect(formatPercentage(0)).toBe('0.00%');
  });

  it('formats negative percentages', () => {
    expect(formatPercentage(-3.14)).toBe('-3.14%');
  });

  it('formats with custom decimal places', () => {
    expect(formatPercentage(12.3456, 1)).toBe('12.3%');
  });

  it('formats large percentages', () => {
    expect(formatPercentage(100)).toBe('100.00%');
  });
});

describe('formatLastUpdated', () => {
  it('formats a Date object', () => {
    const date = new Date(2024, 0, 15, 14, 30);
    const result = formatLastUpdated(date);
    expect(result).toContain('January');
    expect(result).toContain('15');
    expect(result).toContain('2024');
  });

  it('formats a valid date string', () => {
    const result = formatLastUpdated('2024-06-15T10:30:00Z');
    expect(result).toContain('2024');
    expect(result).toContain('June') ;
  });

  it('handles invalid date string by falling back to current date', () => {
    const result = formatLastUpdated('not-a-date');
    const today = new Date();
    expect(result).toContain(today.getFullYear().toString());
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

  it('returns green for very small positive', () => {
    expect(getGainLossColorClass(0.01)).toBe('text-green-600');
  });

  it('returns red for very small negative', () => {
    expect(getGainLossColorClass(-0.01)).toBe('text-red-600');
  });
});

describe('formatGainLoss', () => {
  it('formats positive gain with + sign', () => {
    const result = formatGainLoss(500, 10.5);
    expect(result.formatted).toContain('+');
    expect(result.formatted).toContain('$500.00');
    expect(result.formatted).toContain('10.50%');
    expect(result.colorClass).toBe('text-green-600');
  });

  it('formats negative loss', () => {
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

  it('accepts custom currency', () => {
    const result = formatGainLoss(100, 5, 'EUR');
    expect(result.formatted).toContain('100.00');
  });
});
