import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { fetchPortfolio, fetchTransactions, ApiError } from '../../services/api';

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('ApiError', () => {
  it('sets name, message, status, statusText', () => {
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
      totalValue: 125000,
      totalGainLoss: 8250,
      totalGainLossPercent: 7.02,
      holdings: [],
      lastUpdated: 'June 10, 2024',
    };
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    });

    const result = await fetchPortfolio('1234567890');
    expect(result).toEqual(mockData);
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/portfolio/1234567890');
  });

  it('throws ApiError on 400 response', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({ detail: 'Invalid account' }),
    });

    await expect(fetchPortfolio('bad')).rejects.toThrow(ApiError);
    await expect(fetchPortfolio('bad')).rejects.toThrow('Invalid account');
  });

  it('throws ApiError on non-400 error', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    });

    await expect(fetchPortfolio('123')).rejects.toThrow(ApiError);
  });

  it('throws ApiError on network error', async () => {
    mockFetch.mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(fetchPortfolio('123')).rejects.toThrow(ApiError);
    await expect(fetchPortfolio('123')).rejects.toThrow('Unable to connect');
  });

  it('throws ApiError on unexpected error', async () => {
    mockFetch.mockRejectedValue(new Error('unexpected'));

    await expect(fetchPortfolio('123')).rejects.toThrow(ApiError);
    await expect(fetchPortfolio('123')).rejects.toThrow('unexpected error');
  });
});

describe('fetchTransactions', () => {
  it('returns transaction data on success', async () => {
    const mockData = {
      accountNumber: '1234567890',
      transactions: [],
      message: 'placeholder',
    };
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    });

    const result = await fetchTransactions('1234567890');
    expect(result).toEqual(mockData);
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/transactions/1234567890');
  });

  it('throws ApiError on 400 response', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({ detail: 'Invalid' }),
    });

    await expect(fetchTransactions('bad')).rejects.toThrow(ApiError);
  });

  it('throws ApiError on non-400 error', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Server Error',
    });

    await expect(fetchTransactions('123')).rejects.toThrow(ApiError);
  });

  it('throws ApiError on network error', async () => {
    mockFetch.mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(fetchTransactions('123')).rejects.toThrow('Unable to connect');
  });

  it('throws ApiError on unexpected error', async () => {
    mockFetch.mockRejectedValue(new Error('unexpected'));

    await expect(fetchTransactions('123')).rejects.toThrow('unexpected error');
  });
});
