import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ApiError, fetchPortfolio, fetchTransactions } from './api';

// Mock global fetch
const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

beforeEach(() => {
  mockFetch.mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('ApiError', () => {
  it('creates an error with message only', () => {
    const err = new ApiError('something went wrong');
    expect(err.message).toBe('something went wrong');
    expect(err.name).toBe('ApiError');
    expect(err.status).toBeUndefined();
    expect(err.statusText).toBeUndefined();
  });

  it('creates an error with status and statusText', () => {
    const err = new ApiError('not found', 404, 'Not Found');
    expect(err.message).toBe('not found');
    expect(err.status).toBe(404);
    expect(err.statusText).toBe('Not Found');
  });

  it('is an instance of Error', () => {
    const err = new ApiError('test');
    expect(err).toBeInstanceOf(Error);
    expect(err).toBeInstanceOf(ApiError);
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
      json: () => Promise.resolve(mockData),
    });

    const result = await fetchPortfolio('1234567890');
    expect(result).toEqual(mockData);
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/portfolio/1234567890'
    );
  });

  it('throws ApiError with detail on 400 response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({ detail: 'Invalid account number' }),
    });

    await expect(fetchPortfolio('bad')).rejects.toThrow('Invalid account number');
  });

  it('throws ApiError on other HTTP errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    });

    await expect(fetchPortfolio('1234567890')).rejects.toThrow(ApiError);
  });

  it('throws ApiError when fetch fails (network error)', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

    await expect(fetchPortfolio('1234567890')).rejects.toThrow(
      'Unable to connect to the server'
    );
  });

  it('throws generic ApiError on unexpected errors', async () => {
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
      transactions: [{ id: 1 }],
      message: 'Success',
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });

    const result = await fetchTransactions('1234567890');
    expect(result).toEqual(mockData);
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/transactions/1234567890'
    );
  });

  it('throws ApiError with detail on 400 response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({ detail: 'Invalid account' }),
    });

    await expect(fetchTransactions('bad')).rejects.toThrow('Invalid account');
  });

  it('throws ApiError on other HTTP errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
    });

    await expect(fetchTransactions('1234567890')).rejects.toThrow(ApiError);
  });

  it('throws connection error on fetch failure', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

    await expect(fetchTransactions('1234567890')).rejects.toThrow(
      'Unable to connect to the server'
    );
  });

  it('throws generic error on unexpected failures', async () => {
    mockFetch.mockRejectedValueOnce(new Error('unexpected'));

    await expect(fetchTransactions('1234567890')).rejects.toThrow(
      'An unexpected error occurred while fetching transaction data.'
    );
  });
});
