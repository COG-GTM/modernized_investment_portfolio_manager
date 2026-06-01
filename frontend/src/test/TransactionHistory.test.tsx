import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ToastProvider } from '../contexts/ToastContext';
import TransactionHistory from '../pages/TransactionHistory';

// Mock auth
vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { username: 'testuser', token: 'token' },
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

// Mock API
vi.mock('../services/api', () => ({
  portfolioApi: {
    getPortfolio: vi.fn(),
    getHistory: vi.fn(),
  },
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

function renderHistory(path: string = '/portfolios/1234567890/history') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <ToastProvider>
        <Routes>
          <Route path="/portfolios/:id/history" element={<TransactionHistory />} />
        </Routes>
      </ToastProvider>
    </MemoryRouter>
  );
}

describe('TransactionHistory', () => {
  it('renders the page header', async () => {
    const { portfolioApi } = await import('../services/api');
    vi.mocked(portfolioApi.getHistory).mockResolvedValue({
      accountNumber: '1234567890',
      transactions: [],
      message: 'No transactions found',
      currentPage: 1,
      totalPages: 1,
      totalItems: 0,
    });

    renderHistory();

    await waitFor(() => {
      expect(screen.getByText('Transaction History Inquiry')).toBeInTheDocument();
    });
  });

  it('shows empty state when no transactions', async () => {
    const { portfolioApi } = await import('../services/api');
    vi.mocked(portfolioApi.getHistory).mockResolvedValue({
      accountNumber: '1234567890',
      transactions: [],
      message: '',
      currentPage: 1,
      totalPages: 1,
      totalItems: 0,
    });

    renderHistory();

    await waitFor(() => {
      expect(screen.getByText('No transactions found for this account.')).toBeInTheDocument();
    });
  });

  it('displays transactions in a table', async () => {
    const { portfolioApi } = await import('../services/api');
    vi.mocked(portfolioApi.getHistory).mockResolvedValue({
      accountNumber: '1234567890',
      transactions: [
        { date: '2024-01-15', type: 'BUY', units: 100, price: 150.0, amount: 15000.0, transactionId: 'TX001' },
        { date: '2024-01-14', type: 'SELL', units: 50, price: 145.0, amount: 7250.0, transactionId: 'TX002' },
      ],
      message: 'Transaction history loaded',
      currentPage: 1,
      totalPages: 1,
      totalItems: 2,
    });

    renderHistory();

    await waitFor(() => {
      expect(screen.getByText('Date')).toBeInTheDocument();
      expect(screen.getByText('Type')).toBeInTheDocument();
      expect(screen.getByText('Units')).toBeInTheDocument();
      expect(screen.getByText('Price')).toBeInTheDocument();
      expect(screen.getByText('Amount')).toBeInTheDocument();
    });

    expect(screen.getByText('BUY')).toBeInTheDocument();
    expect(screen.getByText('SELL')).toBeInTheDocument();
  });

  it('shows pagination when multiple pages exist', async () => {
    const { portfolioApi } = await import('../services/api');
    vi.mocked(portfolioApi.getHistory).mockResolvedValue({
      accountNumber: '1234567890',
      transactions: [
        { date: '2024-01-15', type: 'BUY', units: 100, price: 150.0, amount: 15000.0, transactionId: 'TX001' },
      ],
      message: '',
      currentPage: 1,
      totalPages: 3,
      totalItems: 25,
    });

    renderHistory();

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
      expect(screen.getByText('Next PF8')).toBeInTheDocument();
    });
  });

  it('shows error state on API failure', async () => {
    const { portfolioApi, ApiError } = await import('../services/api');
    vi.mocked(portfolioApi.getHistory).mockRejectedValue(
      new ApiError('Server error', 500)
    );

    renderHistory();

    await waitFor(() => {
      // Error appears in both the alert banner and the toast notification
      const errorElements = screen.getAllByText('Server error');
      expect(errorElements.length).toBeGreaterThanOrEqual(1);
    });
  });
});
