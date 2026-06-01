import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ApiError, fetchPortfolio, fetchTransactions } from '../../services/api';

describe('ApiError', () => {
  it('creates an error with message', () => {
    const error = new ApiError('test error');
    expect(error.message).toBe('test error');
    expect(error.name).toBe('ApiError');
  });

  it('creates an error with status and statusText', () => {
    const error = new ApiError('not found', 404, 'Not Found');
    expect(error.status).toBe(404);
    expect(error.statusText).toBe('Not Found');
  });

  it('is an instance of Error', () => {
    const error = new ApiError('test');
    expect(error).toBeInstanceOf(Error);
    expect(error).toBeInstanceOf(ApiError);
  });
});

describe('fetchPortfolio', () => {
  const mockPortfolio = {
    accountNumber: '1234567890',
    totalValue: 125750.50,
    totalGainLoss: 8250.50,
    totalGainLossPercent: 7.02,
    holdings: [],
    lastUpdated: 'January 15, 2024',
  };

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns portfolio data on success', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockPortfolio),
    });

    const result = await fetchPortfolio('1234567890');
    expect(result).toEqual(mockPortfolio);
    expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/portfolio/1234567890');
  });

  it('throws ApiError with detail on 400 response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({ detail: 'Invalid account number' }),
    });

    await expect(fetchPortfolio('bad')).rejects.toThrow(ApiError);
    await expect(fetchPortfolio('bad')).rejects.toThrow('Invalid account number');
  });

  it('throws ApiError on non-400 error response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.resolve({}),
    });

    await expect(fetchPortfolio('1234567890')).rejects.toThrow('HTTP 500: Internal Server Error');
  });

  it('throws connection error on fetch TypeError', async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError('fetch failed'));

    await expect(fetchPortfolio('1234567890')).rejects.toThrow(
      'Unable to connect to the server'
    );
  });

  it('throws generic error on unknown error', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('unknown'));

    await expect(fetchPortfolio('1234567890')).rejects.toThrow(
      'An unexpected error occurred while fetching portfolio data.'
    );
  });
});

describe('fetchTransactions', () => {
  const mockTransactions = {
    accountNumber: '1234567890',
    transactions: [],
    message: 'Transaction history endpoint - placeholder implementation',
  };

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns transaction data on success', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockTransactions),
    });

    const result = await fetchTransactions('1234567890');
    expect(result).toEqual(mockTransactions);
    expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/transactions/1234567890');
  });

  it('throws ApiError with detail on 400 response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({ detail: 'Invalid account' }),
    });

    await expect(fetchTransactions('bad')).rejects.toThrow('Invalid account');
  });

  it('throws ApiError on non-400 error response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
      json: () => Promise.resolve({}),
    });

    await expect(fetchTransactions('1234567890')).rejects.toThrow(
      'HTTP 503: Service Unavailable'
    );
  });

  it('throws connection error on fetch TypeError', async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError('fetch failed'));

    await expect(fetchTransactions('1234567890')).rejects.toThrow(
      'Unable to connect to the server'
    );
  });

  it('throws generic error on unknown error', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('unknown'));

    await expect(fetchTransactions('1234567890')).rejects.toThrow(
      'An unexpected error occurred while fetching transaction data.'
    );
  });
});
