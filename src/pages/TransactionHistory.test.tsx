import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import TransactionHistory from './TransactionHistory';

vi.mock('../services/api', () => ({
  fetchTransactions: vi.fn(),
  ApiError: class ApiError extends Error {
    status?: number;
    statusText?: string;
    constructor(message: string, status?: number, statusText?: string) {
      super(message);
      this.name = 'ApiError';
      this.status = status;
      this.statusText = statusText;
    }
  },
}));

import { fetchTransactions, ApiError } from '../services/api';
const mockFetchTransactions = vi.mocked(fetchTransactions);

function renderTransactionHistory(url = '/transaction-history') {
  return render(
    <MemoryRouter initialEntries={[url]}>
      <TransactionHistory />
    </MemoryRouter>
  );
}

describe('TransactionHistory', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders page title', async () => {
    renderTransactionHistory();
    expect(screen.getByText('Transaction History')).toBeInTheDocument();
  });

  it('renders subtitle', () => {
    renderTransactionHistory();
    expect(
      screen.getByText('Review your investment transaction activity')
    ).toBeInTheDocument();
  });

  it('renders back to main menu link', () => {
    renderTransactionHistory();
    expect(screen.getByText('← Back to Main Menu')).toBeInTheDocument();
  });

  it('shows loading skeleton initially with account param', async () => {
    mockFetchTransactions.mockImplementation(
      () => new Promise(() => {}) // never resolves
    );
    renderTransactionHistory('/transaction-history?account=1234567890');
    expect(document.querySelector('.animate-pulse')).toBeTruthy();
  });

  it('shows message when no account param', async () => {
    renderTransactionHistory('/transaction-history');
    await waitFor(() => {
      expect(
        screen.getByText(/This page will display a comprehensive list/i)
      ).toBeInTheDocument();
    });
  });

  it('shows transactions data after loading with account param', async () => {
    mockFetchTransactions.mockResolvedValue({
      accountNumber: '1234567890',
      transactions: [],
      message: 'No transactions found',
    } as any);

    renderTransactionHistory('/transaction-history?account=1234567890');

    await waitFor(() => {
      expect(screen.getByText('No transactions found')).toBeInTheDocument();
    });
  });

  it('shows no transactions message', async () => {
    mockFetchTransactions.mockResolvedValue({
      accountNumber: '1234567890',
      transactions: [],
      message: 'No transactions',
    } as any);

    renderTransactionHistory('/transaction-history?account=1234567890');

    await waitFor(() => {
      expect(
        screen.getByText('No transactions found for this account.')
      ).toBeInTheDocument();
    });
  });

  it('shows error on ApiError', async () => {
    const { ApiError: ApiErrorClass } = await import('../services/api');
    mockFetchTransactions.mockRejectedValue(
      new ApiErrorClass('Server error', 500)
    );

    renderTransactionHistory('/transaction-history?account=1234567890');

    await waitFor(() => {
      expect(screen.getByText('Server error')).toBeInTheDocument();
    });
  });

  it('shows generic error on unknown error', async () => {
    mockFetchTransactions.mockRejectedValue(new Error('oops'));

    renderTransactionHistory('/transaction-history?account=1234567890');

    await waitFor(() => {
      expect(
        screen.getByText(
          'An unexpected error occurred while loading transactions.'
        )
      ).toBeInTheDocument();
    });
  });

  it('renders transaction list when transactions exist', async () => {
    mockFetchTransactions.mockResolvedValue({
      accountNumber: '1234567890',
      transactions: [{ type: 'BU', amount: 1000, date: '2024-06-01' }],
      message: '1 transaction found',
    } as any);

    renderTransactionHistory('/transaction-history?account=1234567890');

    await waitFor(() => {
      expect(screen.getByText('1 transaction found')).toBeInTheDocument();
    });
  });

  it('displays account number in heading', async () => {
    mockFetchTransactions.mockResolvedValue({
      accountNumber: '1234567890',
      transactions: [],
      message: 'None',
    } as any);

    renderTransactionHistory('/transaction-history?account=1234567890');

    await waitFor(() => {
      expect(
        screen.getByText('Transactions for Account 1234567890')
      ).toBeInTheDocument();
    });
  });

  it('shows feature list when no account', async () => {
    renderTransactionHistory('/transaction-history');
    await waitFor(() => {
      expect(screen.getByText(/Buy\/sell transactions/)).toBeInTheDocument();
      expect(screen.getByText(/Dividend payments/)).toBeInTheDocument();
      expect(screen.getByText(/Fee and commission details/)).toBeInTheDocument();
    });
  });
});
