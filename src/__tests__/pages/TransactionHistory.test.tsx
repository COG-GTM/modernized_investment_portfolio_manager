import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import TransactionHistory from '../../pages/TransactionHistory';

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('TransactionHistory', () => {
  it('renders page title', () => {
    render(
      <MemoryRouter>
        <TransactionHistory />
      </MemoryRouter>
    );
    expect(screen.getByText('Transaction History')).toBeInTheDocument();
  });

  it('renders back button', () => {
    render(
      <MemoryRouter>
        <TransactionHistory />
      </MemoryRouter>
    );
    expect(screen.getByText('← Back to Main Menu')).toBeInTheDocument();
  });

  it('shows placeholder when no account', async () => {
    render(
      <MemoryRouter initialEntries={['/transaction-history']}>
        <TransactionHistory />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/provide an account number/i)).toBeInTheDocument();
    });
  });

  it('fetches transactions when account is in query param', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          accountNumber: '1234567890',
          transactions: [],
          message: 'Placeholder endpoint',
        }),
    });

    render(
      <MemoryRouter initialEntries={['/transaction-history?account=1234567890']}>
        <TransactionHistory />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/transactions/1234567890'
      );
    });

    await waitFor(() => {
      expect(screen.getByText('No transactions found for this account.')).toBeInTheDocument();
    });
  });

  it('shows error on API failure', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    });

    render(
      <MemoryRouter initialEntries={['/transaction-history?account=1234567890']}>
        <TransactionHistory />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  it('shows error on network failure', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

    render(
      <MemoryRouter initialEntries={['/transaction-history?account=1234567890']}>
        <TransactionHistory />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });
});
