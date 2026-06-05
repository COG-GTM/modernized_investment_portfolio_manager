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
  it('formats USD value', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56');
  });

  it('formats with custom currency', () => {
    const result = formatCurrency(1000, 'EUR');
    expect(result).toContain('1,000.00');
  });

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('$0.00');
  });

  it('formats negative value', () => {
    const result = formatCurrency(-500.5);
    expect(result).toContain('500.50');
  });

  it('respects custom options', () => {
    const result = formatCurrency(1234.5678, 'USD', { maximumFractionDigits: 4 });
    expect(result).toContain('1,234.5678');
  });
});

describe('formatNumber', () => {
  it('formats with default 2 decimals', () => {
    expect(formatNumber(1234.5678)).toBe('1,234.57');
  });

  it('formats with 0 decimals', () => {
    expect(formatNumber(1234.5, 0)).toBe('1,235');
  });

  it('formats with custom decimals', () => {
    expect(formatNumber(1234.5678, 4)).toBe('1,234.5678');
  });

  it('formats zero', () => {
    expect(formatNumber(0, 2)).toBe('0.00');
  });
});

describe('formatPercentage', () => {
  it('formats positive percentage', () => {
    expect(formatPercentage(8.97)).toBe('8.97%');
  });

  it('formats negative percentage', () => {
    expect(formatPercentage(-3.5)).toBe('-3.50%');
  });

  it('formats zero', () => {
    expect(formatPercentage(0)).toBe('0.00%');
  });

  it('formats with custom decimals', () => {
    expect(formatPercentage(8.975, 3)).toBe('8.975%');
  });
});

describe('formatLastUpdated', () => {
  it('formats date object', () => {
    const d = new Date(2024, 5, 1, 14, 30);
    const result = formatLastUpdated(d);
    expect(result).toContain('June');
    expect(result).toContain('2024');
  });

  it('formats valid date string', () => {
    const result = formatLastUpdated('2024-06-01T14:30:00');
    expect(result).toContain('2024');
  });

  it('handles invalid date string', () => {
    const result = formatLastUpdated('not a date');
    expect(result).toBeTruthy();
  });
});

describe('getGainLossColorClass', () => {
  it('returns green for positive', () => {
    expect(getGainLossColorClass(100)).toBe('text-green-600');
  });

  it('returns red for negative', () => {
    expect(getGainLossColorClass(-100)).toBe('text-red-600');
  });

  it('returns gray for zero', () => {
    expect(getGainLossColorClass(0)).toBe('text-gray-600');
  });
});

describe('formatGainLoss', () => {
  it('formats positive gain', () => {
    const result = formatGainLoss(1000, 5.5, 'USD');
    expect(result.formatted).toContain('+');
    expect(result.formatted).toContain('1,000.00');
    expect(result.formatted).toContain('5.50%');
    expect(result.colorClass).toBe('text-green-600');
  });

  it('formats negative loss', () => {
    const result = formatGainLoss(-500, -2.5);
    expect(result.formatted).toContain('500.00');
    expect(result.formatted).toContain('2.50%');
    expect(result.colorClass).toBe('text-red-600');
  });

  it('formats zero', () => {
    const result = formatGainLoss(0, 0);
    expect(result.formatted).toContain('0.00');
    expect(result.colorClass).toBe('text-gray-600');
  });
});
