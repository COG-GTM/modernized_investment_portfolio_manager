import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { fetchPortfolio, fetchTransactions, ApiError } from './api';

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('ApiError', () => {
  it('creates an error with name ApiError', () => {
    const err = new ApiError('test error', 400, 'Bad Request');
    expect(err.name).toBe('ApiError');
    expect(err.message).toBe('test error');
    expect(err.status).toBe(400);
    expect(err.statusText).toBe('Bad Request');
  });

  it('is an instance of Error', () => {
    const err = new ApiError('test');
    expect(err).toBeInstanceOf(Error);
  });
});

describe('fetchPortfolio', () => {
  it('returns portfolio data on success', async () => {
    const mockData = {
      accountNumber: '1234567890',
      totalValue: 100000,
      totalGainLoss: 5000,
      totalGainLossPercent: 5.0,
      holdings: [],
      lastUpdated: '2024-01-01',
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    });

    const result = await fetchPortfolio('1234567890');
    expect(result).toEqual(mockData);
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/portfolio/1234567890');
  });

  it('throws ApiError with detail on 400 response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: async () => ({ detail: 'Invalid account' }),
    });

    await expect(fetchPortfolio('bad')).rejects.toThrow('Invalid account');
  });

  it('throws ApiError on non-400 error response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => ({}),
    });

    await expect(fetchPortfolio('1234567890')).rejects.toThrow(ApiError);
  });

  it('throws connection error when fetch fails with TypeError', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('fetch failed'));

    await expect(fetchPortfolio('1234567890')).rejects.toThrow(
      'Unable to connect to the server'
    );
  });

  it('throws generic error for other failures', async () => {
    mockFetch.mockRejectedValueOnce(new Error('random error'));

    await expect(fetchPortfolio('1234567890')).rejects.toThrow(
      'An unexpected error occurred while fetching portfolio data.'
    );
  });
});

describe('fetchTransactions', () => {
  it('returns transaction data on success', async () => {
    const mockData = {
      accountNumber: '1234567890',
      transactions: [],
      message: 'OK',
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    });

    const result = await fetchTransactions('1234567890');
    expect(result).toEqual(mockData);
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/transactions/1234567890');
  });

  it('throws ApiError with detail on 400 response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: async () => ({ detail: 'Invalid account number' }),
    });

    await expect(fetchTransactions('bad')).rejects.toThrow('Invalid account number');
  });

  it('throws ApiError on non-400 error response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({}),
    });

    await expect(fetchTransactions('1234567890')).rejects.toThrow(ApiError);
  });

  it('throws connection error when fetch fails with TypeError', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('fetch failed'));

    await expect(fetchTransactions('1234567890')).rejects.toThrow(
      'Unable to connect to the server'
    );
  });

  it('throws generic error for other failures', async () => {
    mockFetch.mockRejectedValueOnce(new Error('something broke'));

    await expect(fetchTransactions('1234567890')).rejects.toThrow(
      'An unexpected error occurred while fetching transaction data.'
    );
  });
});
