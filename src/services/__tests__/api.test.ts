import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ApiError, fetchPortfolio, fetchTransactions } from '../api';

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('ApiError', () => {
  it('creates an error with message only', () => {
    const err = new ApiError('Something went wrong');
    expect(err.message).toBe('Something went wrong');
    expect(err.name).toBe('ApiError');
    expect(err.status).toBeUndefined();
    expect(err.statusText).toBeUndefined();
    expect(err).toBeInstanceOf(Error);
    expect(err).toBeInstanceOf(ApiError);
  });

  it('creates an error with status and statusText', () => {
    const err = new ApiError('Not found', 404, 'Not Found');
    expect(err.message).toBe('Not found');
    expect(err.status).toBe(404);
    expect(err.statusText).toBe('Not Found');
  });
});

describe('fetchPortfolio', () => {
  it('returns portfolio data on success', async () => {
    const mockData = {
      accountNumber: '1234567890',
      totalValue: 50000,
      totalGainLoss: 1500,
      totalGainLossPercent: 3.1,
      holdings: [],
      lastUpdated: '2024-01-01T00:00:00Z',
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
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
      json: () => Promise.resolve({ detail: 'Invalid account format' }),
    });

    await expect(fetchPortfolio('bad')).rejects.toThrow('Invalid account format');
  });

  it('throws ApiError with fallback message on 400 without detail', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({}),
    });

    await expect(fetchPortfolio('bad')).rejects.toThrow('Invalid account number');
  });

  it('throws ApiError on non-400 HTTP errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    });

    await expect(fetchPortfolio('1234567890')).rejects.toThrow('HTTP 500: Internal Server Error');
  });

  it('throws connection error on fetch TypeError', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

    await expect(fetchPortfolio('1234567890')).rejects.toThrow(
      'Unable to connect to the server'
    );
  });

  it('throws generic error on unexpected errors', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Something else'));

    await expect(fetchPortfolio('1234567890')).rejects.toThrow(
      'An unexpected error occurred while fetching portfolio data.'
    );
  });
});

describe('fetchTransactions', () => {
  it('returns transaction data on success', async () => {
    const mockData = {
      accountNumber: '1234567890',
      transactions: [{ id: 1, type: 'BUY' }],
      message: 'OK',
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
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
      json: () => Promise.resolve({ detail: 'Account not found' }),
    });

    await expect(fetchTransactions('bad')).rejects.toThrow('Account not found');
  });

  it('throws ApiError on non-400 HTTP errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
    });

    await expect(fetchTransactions('1234567890')).rejects.toThrow(
      'HTTP 503: Service Unavailable'
    );
  });

  it('throws connection error on fetch TypeError', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

    await expect(fetchTransactions('1234567890')).rejects.toThrow(
      'Unable to connect to the server'
    );
  });

  it('throws generic error on unexpected errors', async () => {
    mockFetch.mockRejectedValueOnce(new Error('random'));

    await expect(fetchTransactions('1234567890')).rejects.toThrow(
      'An unexpected error occurred while fetching transaction data.'
    );
  });
});
