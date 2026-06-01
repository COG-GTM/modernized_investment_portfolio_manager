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
  it('formats a positive number as USD by default', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56');
  });

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('$0.00');
  });

  it('formats a negative number', () => {
    expect(formatCurrency(-500.1)).toBe('-$500.10');
  });

  it('respects a different currency code', () => {
    const result = formatCurrency(1000, 'EUR');
    expect(result).toContain('1,000.00');
  });

  it('allows overriding fraction digits via options', () => {
    const result = formatCurrency(99.999, 'USD', {
      minimumFractionDigits: 3,
      maximumFractionDigits: 3,
    });
    expect(result).toContain('99.999');
  });

  it('formats large numbers with grouping', () => {
    expect(formatCurrency(1234567.89)).toBe('$1,234,567.89');
  });
});

describe('formatNumber', () => {
  it('formats with default 2 decimal places', () => {
    expect(formatNumber(1234.5678)).toBe('1,234.57');
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
    expect(formatNumber(-42.1)).toBe('-42.10');
  });
});

describe('formatPercentage', () => {
  it('appends % to a formatted number', () => {
    expect(formatPercentage(12.345)).toBe('12.35%');
  });

  it('formats with custom decimal places', () => {
    expect(formatPercentage(99.9, 0)).toBe('100%');
  });

  it('formats zero', () => {
    expect(formatPercentage(0)).toBe('0.00%');
  });

  it('formats negative percentages', () => {
    expect(formatPercentage(-5.5)).toBe('-5.50%');
  });
});

describe('formatLastUpdated', () => {
  it('formats a Date object', () => {
    const date = new Date(2024, 0, 15, 10, 30);
    const result = formatLastUpdated(date);
    expect(result).toContain('January');
    expect(result).toContain('15');
    expect(result).toContain('2024');
  });

  it('formats a valid date string', () => {
    const result = formatLastUpdated('2024-06-15T14:30:00Z');
    expect(result).toContain('2024');
  });

  it('falls back to current date for an invalid string', () => {
    const result = formatLastUpdated('not-a-date');
    const now = new Date();
    expect(result).toContain(String(now.getFullYear()));
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
});

describe('formatGainLoss', () => {
  it('formats a positive gain', () => {
    const { formatted, colorClass } = formatGainLoss(500, 10);
    expect(formatted).toContain('+');
    expect(formatted).toContain('500');
    expect(formatted).toContain('10.00%');
    expect(colorClass).toBe('text-green-600');
  });

  it('formats a negative loss', () => {
    const { formatted, colorClass } = formatGainLoss(-200, -5);
    expect(formatted).toContain('$200.00');
    expect(formatted).toContain('-5.00%');
    expect(colorClass).toBe('text-red-600');
  });

  it('formats zero gain/loss', () => {
    const { formatted, colorClass } = formatGainLoss(0, 0);
    expect(formatted).toContain('0.00');
    expect(colorClass).toBe('text-gray-600');
  });

  it('uses a custom currency', () => {
    const { formatted } = formatGainLoss(100, 5, 'EUR');
    expect(formatted).toContain('100');
  });
});
