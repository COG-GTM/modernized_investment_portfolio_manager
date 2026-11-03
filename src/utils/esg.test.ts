import { describe, expect, it } from 'vitest';
import { formatCarbonIntensity, validateEsgOverride } from './esg';

const REASON = 'Provider restated revenue.';

describe('validateEsgOverride', () => {
  it('accepts a non-negative value and a 10+ character reason', () => {
    expect(validateEsgOverride('70', REASON)).toEqual({});
    expect(validateEsgOverride('0', '1234567890')).toEqual({});
  });

  it('requires a value', () => {
    expect(validateEsgOverride('', REASON).value).toBe('Value is required');
  });

  it('rejects negative values', () => {
    expect(validateEsgOverride('-0.5', REASON).value).toBe('Value must be non-negative');
  });

  it('rejects non-numeric values', () => {
    expect(validateEsgOverride('abc', REASON).value).toBe('Value must be a number');
  });

  it('requires at least 10 characters of reason after trimming', () => {
    expect(validateEsgOverride('1', '').reason).toBe('Reason must be at least 10 characters');
    expect(validateEsgOverride('1', '   123456789   ').reason).toBe('Reason must be at least 10 characters');
  });

  it('counts emoji as one character each, like the server', () => {
    expect(validateEsgOverride('1', '🌍🌍🌍🌍🌍').reason).toBe('Reason must be at least 10 characters');
    expect(validateEsgOverride('1', '🌍🌍🌍🌍🌍🌍🌍🌍🌍🌍')).toEqual({});
  });
});

describe('formatCarbonIntensity', () => {
  it('formats to two decimals and handles missing values', () => {
    expect(formatCarbonIntensity(64.137484)).toBe('64.14');
    expect(formatCarbonIntensity(null)).toBe('—');
  });
});
