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
  it('formats positive USD', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56');
  });

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('$0.00');
  });

  it('formats negative values', () => {
    expect(formatCurrency(-500.5)).toBe('-$500.50');
  });

  it('accepts custom currency', () => {
    const result = formatCurrency(1000, 'EUR');
    expect(result).toContain('1,000.00');
  });

  it('accepts custom options', () => {
    const result = formatCurrency(1234.5678, 'USD', { maximumFractionDigits: 4 });
    expect(result).toContain('1,234.5678');
  });
});

describe('formatNumber', () => {
  it('formats with default 2 decimals', () => {
    expect(formatNumber(1234.5)).toBe('1,234.50');
  });

  it('formats with 0 decimals', () => {
    expect(formatNumber(1234.5, 0)).toBe('1,235');
  });

  it('formats with custom decimals', () => {
    expect(formatNumber(1234.5678, 4)).toBe('1,234.5678');
  });

  it('formats zero', () => {
    expect(formatNumber(0)).toBe('0.00');
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
    expect(formatPercentage(12.345, 1)).toBe('12.3%');
  });
});

describe('formatLastUpdated', () => {
  it('formats a Date object', () => {
    const d = new Date(2024, 5, 1, 14, 30);
    const result = formatLastUpdated(d);
    expect(result).toContain('June');
    expect(result).toContain('2024');
  });

  it('formats a valid date string', () => {
    const result = formatLastUpdated('2024-06-01T14:30:00');
    expect(result).toContain('2024');
  });

  it('handles invalid date string gracefully', () => {
    const result = formatLastUpdated('not-a-date');
    expect(typeof result).toBe('string');
    expect(result.length).toBeGreaterThan(0);
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
    const result = formatGainLoss(2000, 8.5);
    expect(result.formatted).toContain('+');
    expect(result.formatted).toContain('2,000.00');
    expect(result.formatted).toContain('8.50%');
    expect(result.colorClass).toBe('text-green-600');
  });

  it('formats negative loss', () => {
    const result = formatGainLoss(-500, -3.5);
    expect(result.formatted).toContain('-');
    expect(result.colorClass).toBe('text-red-600');
  });

  it('formats zero', () => {
    const result = formatGainLoss(0, 0);
    expect(result.colorClass).toBe('text-gray-600');
  });
});
