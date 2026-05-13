import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiError, fetchPortfolio, fetchTransactions } from '../api';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

beforeEach(() => {
  mockFetch.mockReset();
});

describe('ApiError', () => {
  it('sets name, message, status, and statusText', () => {
    const error = new ApiError('Something went wrong', 404, 'Not Found');
    expect(error.name).toBe('ApiError');
    expect(error.message).toBe('Something went wrong');
    expect(error.status).toBe(404);
    expect(error.statusText).toBe('Not Found');
    expect(error).toBeInstanceOf(Error);
  });
});

describe('fetchPortfolio', () => {
  it('returns portfolio data on successful fetch', async () => {
    const mockData = {
      accountNumber: '1234567890',
      totalValue: 100000,
      totalGainLoss: 5000,
      totalGainLossPercent: 5.26,
      holdings: [],
      lastUpdated: '2024-01-15T10:30:00Z',
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
      json: () => Promise.resolve({ detail: 'Invalid account number format' }),
    });

    await expect(fetchPortfolio('bad')).rejects.toThrow(ApiError);
    await mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({ detail: 'Invalid account number format' }),
    });

    try {
      await fetchPortfolio('bad');
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).message).toBe('Invalid account number format');
      expect((e as ApiError).status).toBe(400);
    }
  });

  it('throws ApiError on non-400 error response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    });

    try {
      await fetchPortfolio('1234567890');
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).message).toBe('HTTP 500: Internal Server Error');
      expect((e as ApiError).status).toBe(500);
    }
  });

  it('throws connection error on TypeError with fetch', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

    try {
      await fetchPortfolio('1234567890');
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).message).toBe(
        'Unable to connect to the server. Please ensure the backend is running.'
      );
    }
  });
});

describe('fetchTransactions', () => {
  it('returns transaction data on successful fetch', async () => {
    const mockData = {
      accountNumber: '1234567890',
      transactions: [{ id: 1, type: 'BUY', amount: 1000 }],
      message: 'Success',
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
      json: () => Promise.resolve({ detail: 'Invalid account number' }),
    });

    try {
      await fetchTransactions('bad');
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).message).toBe('Invalid account number');
      expect((e as ApiError).status).toBe(400);
    }
  });

  it('throws ApiError on non-400 error response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
    });

    try {
      await fetchTransactions('1234567890');
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).message).toBe('HTTP 503: Service Unavailable');
      expect((e as ApiError).status).toBe(503);
    }
  });

  it('throws connection error on TypeError with fetch', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

    try {
      await fetchTransactions('1234567890');
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).message).toBe(
        'Unable to connect to the server. Please ensure the backend is running.'
      );
    }
  });
});
