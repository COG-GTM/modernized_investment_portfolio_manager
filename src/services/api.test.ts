import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { fetchPortfolio, fetchTransactions, ApiError } from './api';

const mockPortfolio = {
  accountNumber: '1234567890',
  totalValue: 125750.5,
  totalGainLoss: 8250.5,
  totalGainLossPercent: 7.02,
  holdings: [
    {
      symbol: 'AAPL',
      name: 'Apple Inc.',
      shares: 150,
      currentPrice: 185.25,
      marketValue: 27787.5,
      gainLoss: 2287.5,
      gainLossPercent: 8.97,
    },
  ],
  lastUpdated: 'June 1, 2024',
};

const mockTransactions = {
  accountNumber: '1234567890',
  transactions: [{ type: 'BU', amount: 1000 }],
  message: '1 transaction found',
};

describe('ApiError', () => {
  it('creates error with message', () => {
    const error = new ApiError('Test error');
    expect(error.message).toBe('Test error');
    expect(error.name).toBe('ApiError');
  });

  it('creates error with status', () => {
    const error = new ApiError('Not found', 404, 'Not Found');
    expect(error.status).toBe(404);
    expect(error.statusText).toBe('Not Found');
  });

  it('is an instance of Error', () => {
    const error = new ApiError('Test');
    expect(error instanceof Error).toBe(true);
  });
});

describe('fetchPortfolio', () => {
  beforeEach(() => {
    vi.resetAllMocks();
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
    expect(result.accountNumber).toBe('1234567890');
    expect(result.totalValue).toBe(125750.5);
  });

  it('throws ApiError on 400 with detail', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({ detail: 'Invalid account number' }),
    });
    await expect(fetchPortfolio('bad')).rejects.toThrow(ApiError);
    try {
      await fetchPortfolio('bad');
    } catch (e) {
      expect((e as ApiError).message).toBe('Invalid account number');
      expect((e as ApiError).status).toBe(400);
    }
  });

  it('throws ApiError on 400 without detail', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({}),
    });
    await expect(fetchPortfolio('bad')).rejects.toThrow(ApiError);
  });

  it('throws ApiError on 500', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    });
    await expect(fetchPortfolio('123')).rejects.toThrow(ApiError);
    try {
      await fetchPortfolio('123');
    } catch (e) {
      expect((e as ApiError).message).toContain('500');
    }
  });

  it('throws ApiError on network error', async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));
    await expect(fetchPortfolio('123')).rejects.toThrow(ApiError);
    try {
      await fetchPortfolio('123');
    } catch (e) {
      expect((e as ApiError).message).toContain('Unable to connect');
    }
  });

  it('calls fetch with correct URL', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockPortfolio),
    });
    await fetchPortfolio('9999999999');
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/portfolio/9999999999')
    );
  });
});

describe('fetchTransactions', () => {
  beforeEach(() => {
    vi.resetAllMocks();
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
    expect(result.accountNumber).toBe('1234567890');
    expect(result.transactions).toHaveLength(1);
  });

  it('throws ApiError on 400', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({ detail: 'Invalid' }),
    });
    await expect(fetchTransactions('bad')).rejects.toThrow(ApiError);
  });

  it('throws ApiError on non-400 error', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Server Error',
    });
    await expect(fetchTransactions('123')).rejects.toThrow(ApiError);
  });

  it('throws ApiError on network error', async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));
    await expect(fetchTransactions('123')).rejects.toThrow(ApiError);
  });

  it('calls fetch with correct URL', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockTransactions),
    });
    await fetchTransactions('9999999999');
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/transactions/9999999999')
    );
  });
});
