import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ApiError, fetchPortfolio, fetchTransactions } from '../api'

describe('ApiError', () => {
  it('sets name, status, and statusText', () => {
    const error = new ApiError('Not Found', 404, 'Not Found')
    expect(error.name).toBe('ApiError')
    expect(error.message).toBe('Not Found')
    expect(error.status).toBe(404)
    expect(error.statusText).toBe('Not Found')
  })

  it('is an instance of Error', () => {
    const error = new ApiError('test')
    expect(error).toBeInstanceOf(Error)
  })
})

describe('fetchPortfolio', () => {
  const mockPortfolio = {
    accountNumber: '1234567890',
    totalValue: 50000,
    totalGainLoss: 5000,
    totalGainLossPercent: 10,
    holdings: [],
    lastUpdated: '2024-01-01',
  }

  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns portfolio data on successful fetch', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockPortfolio),
    } as Response)

    const result = await fetchPortfolio('1234567890')
    expect(result).toEqual(mockPortfolio)
    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/portfolio/1234567890'
    )
  })

  it('throws ApiError on HTTP 400', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({ detail: 'Invalid account number' }),
    } as unknown as Response)

    await expect(fetchPortfolio('bad')).rejects.toThrow(ApiError)
    await expect(fetchPortfolio('bad')).rejects.toThrow('Invalid account number')
  })

  it('throws ApiError on HTTP 500', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.resolve({}),
    } as unknown as Response)

    await expect(fetchPortfolio('1234567890')).rejects.toThrow(ApiError)
    await expect(fetchPortfolio('1234567890')).rejects.toThrow(
      'HTTP 500: Internal Server Error'
    )
  })

  it('throws ApiError on network error (TypeError with fetch)', async () => {
    vi.mocked(fetch).mockRejectedValue(new TypeError('Failed to fetch'))

    await expect(fetchPortfolio('1234567890')).rejects.toThrow(ApiError)
    await expect(fetchPortfolio('1234567890')).rejects.toThrow(
      'Unable to connect to the server'
    )
  })
})

describe('fetchTransactions', () => {
  const mockTransactions = {
    accountNumber: '1234567890',
    transactions: [{ id: 1, type: 'BUY', amount: 100 }],
    message: 'Success',
  }

  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns transaction data on successful fetch', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockTransactions),
    } as Response)

    const result = await fetchTransactions('1234567890')
    expect(result).toEqual(mockTransactions)
    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/transactions/1234567890'
    )
  })

  it('throws ApiError on HTTP 400', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({ detail: 'Invalid account number' }),
    } as unknown as Response)

    await expect(fetchTransactions('bad')).rejects.toThrow(ApiError)
    await expect(fetchTransactions('bad')).rejects.toThrow(
      'Invalid account number'
    )
  })

  it('throws ApiError on network error', async () => {
    vi.mocked(fetch).mockRejectedValue(new TypeError('Failed to fetch'))

    await expect(fetchTransactions('1234567890')).rejects.toThrow(ApiError)
    await expect(fetchTransactions('1234567890')).rejects.toThrow(
      'Unable to connect to the server'
    )
  })
})
