import { describe, it, expect, vi } from 'vitest'
import {
  formatCurrency,
  formatNumber,
  formatPercentage,
  formatLastUpdated,
  getGainLossColorClass,
  formatGainLoss,
} from '../format'

describe('formatCurrency', () => {
  it('formats with default USD currency', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56')
  })

  it('formats with custom currency', () => {
    const result = formatCurrency(1234.56, 'EUR')
    expect(result).toContain('1,234.56')
  })

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('$0.00')
  })

  it('formats negative values', () => {
    expect(formatCurrency(-500.99)).toBe('-$500.99')
  })

  it('formats large numbers', () => {
    expect(formatCurrency(1000000)).toBe('$1,000,000.00')
  })
})

describe('formatNumber', () => {
  it('formats with default 2 decimals', () => {
    expect(formatNumber(1234.5678)).toBe('1,234.57')
  })

  it('formats with custom decimals', () => {
    expect(formatNumber(1234.5678, 3)).toBe('1,234.568')
  })

  it('formats zero', () => {
    expect(formatNumber(0)).toBe('0.00')
  })
})

describe('formatPercentage', () => {
  it('formats positive percentage', () => {
    expect(formatPercentage(12.34)).toBe('12.34%')
  })

  it('formats negative percentage', () => {
    expect(formatPercentage(-5.67)).toBe('-5.67%')
  })

  it('formats zero percentage', () => {
    expect(formatPercentage(0)).toBe('0.00%')
  })

  it('formats with custom decimals', () => {
    expect(formatPercentage(12.3456, 1)).toBe('12.3%')
  })
})

describe('formatLastUpdated', () => {
  it('formats a Date object', () => {
    const date = new Date(2024, 0, 15, 14, 30)
    const result = formatLastUpdated(date)
    expect(result).toContain('January')
    expect(result).toContain('15')
    expect(result).toContain('2024')
  })

  it('formats a valid date string', () => {
    const result = formatLastUpdated('2024-06-15T10:30:00Z')
    expect(result).toContain('June')
    expect(result).toContain('15')
    expect(result).toContain('2024')
  })

  it('falls back to current date for invalid date string', () => {
    const now = new Date()
    const result = formatLastUpdated('not-a-date')
    expect(result).toContain(now.getFullYear().toString())
  })
})

describe('getGainLossColorClass', () => {
  it('returns green for positive values', () => {
    expect(getGainLossColorClass(100)).toBe('text-green-600')
  })

  it('returns red for negative values', () => {
    expect(getGainLossColorClass(-50)).toBe('text-red-600')
  })

  it('returns gray for zero', () => {
    expect(getGainLossColorClass(0)).toBe('text-gray-600')
  })
})

describe('formatGainLoss', () => {
  it('formats positive gain', () => {
    const result = formatGainLoss(500, 10.5)
    expect(result.formatted).toContain('+')
    expect(result.formatted).toContain('$500.00')
    expect(result.formatted).toContain('10.50%')
    expect(result.colorClass).toBe('text-green-600')
  })

  it('formats negative loss', () => {
    const result = formatGainLoss(-200, -5.25)
    expect(result.formatted).toContain('-$200.00')
    expect(result.formatted).toContain('-5.25%')
    expect(result.colorClass).toBe('text-red-600')
  })

  it('formats zero value', () => {
    const result = formatGainLoss(0, 0)
    expect(result.formatted).toContain('$0.00')
    expect(result.formatted).toContain('0.00%')
    expect(result.colorClass).toBe('text-gray-600')
  })
})
