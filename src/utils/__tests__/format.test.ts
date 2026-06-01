import { describe, it, expect, vi } from 'vitest';
import {
  formatCurrency,
  formatNumber,
  formatPercentage,
  formatLastUpdated,
  getGainLossColorClass,
  formatGainLoss,
} from '../format';

describe('formatCurrency', () => {
  it('formats a positive number', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56');
  });

  it('formats a negative number', () => {
    expect(formatCurrency(-1234.56)).toBe('-$1,234.56');
  });

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('$0.00');
  });

  it('formats with custom currency (EUR)', () => {
    const result = formatCurrency(1234.56, 'EUR');
    expect(result).toContain('1,234.56');
    expect(result).toContain('€');
  });

  it('formats with custom options', () => {
    const result = formatCurrency(1234.5, 'USD', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    expect(result).toBe('$1,235');
  });
});

describe('formatNumber', () => {
  it('formats with default 2 decimals', () => {
    expect(formatNumber(1234.567)).toBe('1,234.57');
  });

  it('formats with 0 decimals', () => {
    expect(formatNumber(1234.567, 0)).toBe('1,235');
  });

  it('formats with 4 decimals', () => {
    expect(formatNumber(1234.5, 4)).toBe('1,234.5000');
  });

  it('formats large numbers', () => {
    expect(formatNumber(1234567890.12)).toBe('1,234,567,890.12');
  });
});

describe('formatPercentage', () => {
  it('formats a positive percentage', () => {
    expect(formatPercentage(12.34)).toBe('12.34%');
  });

  it('formats a negative percentage', () => {
    expect(formatPercentage(-5.67)).toBe('-5.67%');
  });

  it('formats zero percentage', () => {
    expect(formatPercentage(0)).toBe('0.00%');
  });

  it('formats with custom decimals', () => {
    expect(formatPercentage(12.3456, 3)).toBe('12.346%');
  });
});

describe('formatLastUpdated', () => {
  it('formats a valid Date object', () => {
    const date = new Date('2024-01-15T10:30:00Z');
    const result = formatLastUpdated(date);
    expect(result).toContain('January');
    expect(result).toContain('15');
    expect(result).toContain('2024');
  });

  it('formats a valid date string', () => {
    const result = formatLastUpdated('2024-06-20T14:00:00Z');
    expect(result).toContain('June');
    expect(result).toContain('20');
    expect(result).toContain('2024');
  });

  it('returns current date formatted for an invalid date string', () => {
    const now = new Date();
    const result = formatLastUpdated('not-a-date');
    const currentYear = now.getFullYear().toString();
    expect(result).toContain(currentYear);
  });
});

describe('getGainLossColorClass', () => {
  it('returns text-green-600 for positive values', () => {
    expect(getGainLossColorClass(100)).toBe('text-green-600');
  });

  it('returns text-red-600 for negative values', () => {
    expect(getGainLossColorClass(-50)).toBe('text-red-600');
  });

  it('returns text-gray-600 for zero', () => {
    expect(getGainLossColorClass(0)).toBe('text-gray-600');
  });
});

describe('formatGainLoss', () => {
  it('formats a positive gain with + sign and correct color', () => {
    const result = formatGainLoss(1500, 12.5);
    expect(result.formatted).toContain('+');
    expect(result.formatted).toContain('$1,500.00');
    expect(result.formatted).toContain('12.50%');
    expect(result.colorClass).toBe('text-green-600');
  });

  it('formats a negative loss', () => {
    const result = formatGainLoss(-500, -3.25);
    expect(result.formatted).toContain('-$500.00');
    expect(result.formatted).toContain('-3.25%');
    expect(result.colorClass).toBe('text-red-600');
  });

  it('formats zero gain/loss', () => {
    const result = formatGainLoss(0, 0);
    expect(result.formatted).toContain('$0.00');
    expect(result.formatted).toContain('0.00%');
    expect(result.colorClass).toBe('text-gray-600');
  });
});
