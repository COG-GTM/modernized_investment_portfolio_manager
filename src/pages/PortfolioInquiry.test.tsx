import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import PortfolioInquiry from './PortfolioInquiry';

vi.mock('../services/api', () => ({
  fetchPortfolio: vi.fn(),
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

import { fetchPortfolio, ApiError } from '../services/api';
const mockFetchPortfolio = vi.mocked(fetchPortfolio);

const mockPortfolioData = {
  accountNumber: '1234567890',
  totalValue: 125750.50,
  totalGainLoss: 8250.50,
  totalGainLossPercent: 7.02,
  holdings: [
    {
      symbol: 'AAPL',
      name: 'Apple Inc.',
      shares: 150,
      currentPrice: 185.25,
      marketValue: 27787.50,
      gainLoss: 2287.50,
      gainLossPercent: 8.97,
    },
  ],
  lastUpdated: 'June 1, 2024',
};

function renderPortfolioInquiry() {
  return render(
    <MemoryRouter>
      <PortfolioInquiry />
    </MemoryRouter>
  );
}

describe('PortfolioInquiry', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders page title', () => {
    renderPortfolioInquiry();
    expect(screen.getByText('Portfolio Inquiry')).toBeInTheDocument();
  });

  it('renders subtitle', () => {
    renderPortfolioInquiry();
    expect(
      screen.getByText('Enter your account number to view portfolio details')
    ).toBeInTheDocument();
  });

  it('renders account search heading', () => {
    renderPortfolioInquiry();
    expect(screen.getByText('Account Search')).toBeInTheDocument();
  });

  it('renders back to main menu link', () => {
    renderPortfolioInquiry();
    expect(screen.getByText('← Back to Main Menu')).toBeInTheDocument();
  });

  it('renders submit button', () => {
    renderPortfolioInquiry();
    expect(screen.getByText('View Portfolio')).toBeInTheDocument();
  });

  it('submit button is disabled initially', () => {
    renderPortfolioInquiry();
    const btn = screen.getByText('View Portfolio');
    expect(btn).toBeDisabled();
  });

  it('shows portfolio data after successful submit', async () => {
    mockFetchPortfolio.mockResolvedValue(mockPortfolioData as any);
    renderPortfolioInquiry();

    const input = screen.getByRole('textbox');
    await userEvent.type(input, '1234567890');

    await waitFor(() => {
      expect(screen.getByText('View Portfolio')).not.toBeDisabled();
    });

    fireEvent.click(screen.getByText('View Portfolio'));

    await waitFor(() => {
      expect(screen.getByText('Portfolio Details')).toBeInTheDocument();
    });
  });

  it('shows error on ApiError', async () => {
    const { ApiError: ApiErrorClass } = await import('../services/api');
    mockFetchPortfolio.mockRejectedValue(new ApiErrorClass('Invalid account', 400));
    renderPortfolioInquiry();

    const input = screen.getByRole('textbox');
    await userEvent.type(input, '1234567890');

    await waitFor(() => {
      expect(screen.getByText('View Portfolio')).not.toBeDisabled();
    });

    fireEvent.click(screen.getByText('View Portfolio'));

    await waitFor(() => {
      expect(screen.getByText('Invalid account')).toBeInTheDocument();
    });
  });

  it('shows generic error on unknown error', async () => {
    mockFetchPortfolio.mockRejectedValue(new Error('unknown'));
    renderPortfolioInquiry();

    const input = screen.getByRole('textbox');
    await userEvent.type(input, '1234567890');

    await waitFor(() => {
      expect(screen.getByText('View Portfolio')).not.toBeDisabled();
    });

    fireEvent.click(screen.getByText('View Portfolio'));

    await waitFor(() => {
      expect(
        screen.getByText('An unexpected error occurred. Please try again.')
      ).toBeInTheDocument();
    });
  });

  it('shows holdings after data is loaded', async () => {
    mockFetchPortfolio.mockResolvedValue(mockPortfolioData as any);
    renderPortfolioInquiry();

    const input = screen.getByRole('textbox');
    await userEvent.type(input, '1234567890');

    await waitFor(() => {
      expect(screen.getByText('View Portfolio')).not.toBeDisabled();
    });

    fireEvent.click(screen.getByText('View Portfolio'));

    await waitFor(() => {
      expect(screen.getByText('Holdings')).toBeInTheDocument();
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });
  });

  it('shows View Transaction History link after data loads', async () => {
    mockFetchPortfolio.mockResolvedValue(mockPortfolioData as any);
    renderPortfolioInquiry();

    const input = screen.getByRole('textbox');
    await userEvent.type(input, '1234567890');

    await waitFor(() => {
      expect(screen.getByText('View Portfolio')).not.toBeDisabled();
    });

    fireEvent.click(screen.getByText('View Portfolio'));

    await waitFor(() => {
      expect(screen.getByText('View Transaction History')).toBeInTheDocument();
    });
  });

  it('resets form on New Search', async () => {
    mockFetchPortfolio.mockResolvedValue(mockPortfolioData as any);
    renderPortfolioInquiry();

    const input = screen.getByRole('textbox');
    await userEvent.type(input, '1234567890');

    await waitFor(() => {
      expect(screen.getByText('View Portfolio')).not.toBeDisabled();
    });

    fireEvent.click(screen.getByText('View Portfolio'));

    await waitFor(() => {
      expect(screen.getByText('New Search')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('New Search'));

    await waitFor(() => {
      expect(screen.getByText('Account Search')).toBeInTheDocument();
    });
  });
});
