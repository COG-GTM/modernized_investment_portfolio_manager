import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PortfolioInquiry from '../../pages/PortfolioInquiry';

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch);
});

afterEach(() => {
  vi.restoreAllMocks();
});

function renderPortfolioInquiry() {
  return render(
    <MemoryRouter>
      <PortfolioInquiry />
    </MemoryRouter>
  );
}

describe('PortfolioInquiry', () => {
  it('renders page title', () => {
    renderPortfolioInquiry();
    expect(screen.getByText('Portfolio Inquiry')).toBeInTheDocument();
  });

  it('renders account number input', () => {
    renderPortfolioInquiry();
    expect(screen.getByLabelText('Account Number')).toBeInTheDocument();
  });

  it('renders submit button', () => {
    renderPortfolioInquiry();
    expect(screen.getByText('View Portfolio')).toBeInTheDocument();
  });

  it('renders back button', () => {
    renderPortfolioInquiry();
    expect(screen.getByText('← Back to Main Menu')).toBeInTheDocument();
  });

  it('submit button is initially disabled', () => {
    renderPortfolioInquiry();
    const btn = screen.getByText('View Portfolio');
    expect(btn).toBeDisabled();
  });

  it('shows portfolio data on successful submission', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          accountNumber: '1234567890',
          totalValue: 125000,
          totalGainLoss: 8000,
          totalGainLossPercent: 6.84,
          holdings: [
            {
              symbol: 'AAPL',
              name: 'Apple Inc.',
              shares: 100,
              currentPrice: 185.25,
              marketValue: 18525,
              gainLoss: 3525,
              gainLossPercent: 23.5,
            },
          ],
          lastUpdated: 'June 10, 2024',
        }),
    });

    renderPortfolioInquiry();
    const input = screen.getByLabelText('Account Number');
    fireEvent.change(input, { target: { value: '1234567890' } });

    await waitFor(() => {
      expect(screen.getByText('View Portfolio')).not.toBeDisabled();
    });

    fireEvent.click(screen.getByText('View Portfolio'));

    await waitFor(() => {
      expect(screen.getByText('Portfolio Summary')).toBeInTheDocument();
    });
  });

  it('shows error on API failure', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      json: () => Promise.resolve({ detail: 'Account not found' }),
    });

    renderPortfolioInquiry();
    const input = screen.getByLabelText('Account Number');
    fireEvent.change(input, { target: { value: '1234567890' } });

    await waitFor(() => {
      expect(screen.getByText('View Portfolio')).not.toBeDisabled();
    });

    fireEvent.click(screen.getByText('View Portfolio'));

    await waitFor(() => {
      expect(screen.getByText('Account not found')).toBeInTheDocument();
    });
  });
});
