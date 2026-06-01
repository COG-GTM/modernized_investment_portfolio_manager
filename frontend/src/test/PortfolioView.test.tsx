import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ToastProvider } from '../contexts/ToastContext';
import PortfolioView from '../pages/PortfolioView';

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

function renderPortfolioView(path: string = '/portfolios/lookup') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <ToastProvider>
        <Routes>
          <Route path="/portfolios/:id" element={<PortfolioView />} />
        </Routes>
      </ToastProvider>
    </MemoryRouter>
  );
}

describe('PortfolioView', () => {
  it('renders lookup form when in lookup mode', () => {
    renderPortfolioView('/portfolios/lookup');
    expect(screen.getByText('Portfolio Position Inquiry')).toBeInTheDocument();
    expect(screen.getByLabelText('Account Number')).toBeInTheDocument();
    expect(screen.getByText('View Portfolio')).toBeInTheDocument();
  });

  it('shows loading state when fetching portfolio', async () => {
    const { portfolioApi } = await import('../services/api');
    vi.mocked(portfolioApi.getPortfolio).mockImplementation(
      () => new Promise(() => {}) // never resolves
    );

    renderPortfolioView('/portfolios/1234567890');
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('displays portfolio data after successful fetch', async () => {
    const { portfolioApi } = await import('../services/api');
    vi.mocked(portfolioApi.getPortfolio).mockResolvedValue({
      accountNumber: '1234567890',
      totalValue: 50000,
      totalGainLoss: 5000,
      totalGainLossPercent: 11.11,
      holdings: [
        {
          symbol: 'AAPL',
          name: 'Apple Inc.',
          shares: 100,
          currentPrice: 150.0,
          marketValue: 15000,
          gainLoss: 2000,
          gainLossPercent: 15.38,
        },
      ],
      lastUpdated: '2024-01-15T10:00:00Z',
    });

    renderPortfolioView('/portfolios/1234567890');

    await waitFor(() => {
      expect(screen.getByText('Portfolio Details')).toBeInTheDocument();
      expect(screen.getByText('Account: 1234567890')).toBeInTheDocument();
    });

    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
  });

  it('shows error state when API call fails', async () => {
    const { portfolioApi, ApiError } = await import('../services/api');
    vi.mocked(portfolioApi.getPortfolio).mockRejectedValue(
      new ApiError('Account not found', 404)
    );

    renderPortfolioView('/portfolios/9999999999');

    await waitFor(() => {
      // Error appears in both the alert banner and the toast notification
      const errorElements = screen.getAllByText('Account not found');
      expect(errorElements.length).toBeGreaterThanOrEqual(1);
    });
  });
});
