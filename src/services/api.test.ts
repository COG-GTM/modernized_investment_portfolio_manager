import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { fetchPortfolio, fetchTransactions, ApiError } from './api';

describe('ApiError', () => {
  it('creates an error with message', () => {
    const error = new ApiError('test error');
    expect(error.message).toBe('test error');
    expect(error.name).toBe('ApiError');
    expect(error.status).toBeUndefined();
    expect(error.statusText).toBeUndefined();
  });

  it('creates an error with status and statusText', () => {
    const error = new ApiError('not found', 404, 'Not Found');
    expect(error.message).toBe('not found');
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
    totalValue: 50000,
    totalGainLoss: 5000,
    totalGainLossPercent: 10,
    holdings: [],
    lastUpdated: '2024-01-01T00:00:00Z',
  };

  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns portfolio data on success', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockPortfolio),
    } as Response);

    const result = await fetchPortfolio('1234567890');
    expect(result).toEqual(mockPortfolio);
    expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/portfolio/1234567890');
  });

  it('throws ApiError with detail on 400 response', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({ detail: 'Invalid account number' }),
    } as unknown as Response);

    await expect(fetchPortfolio('bad')).rejects.toThrow(ApiError);
    await expect(fetchPortfolio('bad')).rejects.toThrow('Invalid account number');
  });

  it('throws ApiError on non-400 HTTP errors', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.resolve({}),
    } as unknown as Response);

    await expect(fetchPortfolio('1234567890')).rejects.toThrow(ApiError);
    await expect(fetchPortfolio('1234567890')).rejects.toThrow('HTTP 500');
  });

  it('throws ApiError on network/fetch failure', async () => {
    vi.mocked(fetch).mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(fetchPortfolio('1234567890')).rejects.toThrow(ApiError);
    await expect(fetchPortfolio('1234567890')).rejects.toThrow('Unable to connect to the server');
  });

  it('throws ApiError on unexpected errors', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('Something unexpected'));

    await expect(fetchPortfolio('1234567890')).rejects.toThrow(ApiError);
    await expect(fetchPortfolio('1234567890')).rejects.toThrow('An unexpected error occurred');
  });

  it('uses fallback message when 400 detail is missing', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({}),
    } as unknown as Response);

    await expect(fetchPortfolio('bad')).rejects.toThrow('Invalid account number');
  });
});

describe('fetchTransactions', () => {
  const mockTransactions = {
    accountNumber: '1234567890',
    transactions: [{ id: 1, type: 'BUY', amount: 100 }],
    message: 'Success',
  };

  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns transaction data on success', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockTransactions),
    } as Response);

    const result = await fetchTransactions('1234567890');
    expect(result).toEqual(mockTransactions);
    expect(fetch).toHaveBeenCalledWith('http://localhost:8000/api/transactions/1234567890');
  });

  it('throws ApiError with detail on 400 response', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({ detail: 'Invalid account' }),
    } as unknown as Response);

    await expect(fetchTransactions('bad')).rejects.toThrow('Invalid account');
  });

  it('throws ApiError on non-400 HTTP errors', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 503,
      statusText: 'Service Unavailable',
      json: () => Promise.resolve({}),
    } as unknown as Response);

    await expect(fetchTransactions('1234567890')).rejects.toThrow('HTTP 503');
  });

  it('throws ApiError on network failure', async () => {
    vi.mocked(fetch).mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(fetchTransactions('1234567890')).rejects.toThrow('Unable to connect to the server');
  });

  it('throws ApiError on unexpected errors', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('Oops'));

    await expect(fetchTransactions('1234567890')).rejects.toThrow('An unexpected error occurred while fetching transaction data');
  });
});
