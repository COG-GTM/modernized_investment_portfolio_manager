import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PortfolioSummary from './PortfolioSummary';
import type { Portfolio } from '../types';

const mockPortfolio: Portfolio = {
  portfolioId: 'PORT0001',
  accountNumber: '1234567890',
  totalValue: 100000,
  totalCostBasis: 90000,
  totalGainLoss: 10000,
  totalGainLossPercent: 11.11,
  currency: 'USD',
  positions: [
    {
      portfolioId: 'PORT0001',
      investmentId: 'AAPL123456',
      symbol: 'AAPL',
      name: 'Apple Inc.',
      quantity: 100,
      costBasis: 15000,
      currentPrice: 185,
      marketValue: 18500,
      currency: 'USD',
      status: 'ACTIVE',
      gainLoss: 3500,
      gainLossPercent: 23.33,
      lastUpdated: '2024-06-01',
    },
  ],
  lastUpdated: '2024-06-01T14:30:00',
};

describe('PortfolioSummary', () => {
  it('renders portfolio summary heading', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('Portfolio Summary')).toBeInTheDocument();
  });

  it('renders total value label', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('Total Value')).toBeInTheDocument();
  });

  it('renders total gain/loss label', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('Total Gain/Loss')).toBeInTheDocument();
  });

  it('renders gain/loss % label', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('Gain/Loss %')).toBeInTheDocument();
  });

  it('renders portfolio ID', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('PORT0001')).toBeInTheDocument();
  });

  it('renders account number', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('1234567890')).toBeInTheDocument();
  });

  it('renders positions count', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('renders New Search button when onNewSearch provided', () => {
    const onNewSearch = vi.fn();
    render(<PortfolioSummary portfolio={mockPortfolio} onNewSearch={onNewSearch} />);
    const btn = screen.getByText('New Search');
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(onNewSearch).toHaveBeenCalledOnce();
  });

  it('does not render New Search button when onNewSearch not provided', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.queryByText('New Search')).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <PortfolioSummary portfolio={mockPortfolio} className="my-class" />
    );
    expect(container.innerHTML).toContain('my-class');
  });

  it('applies green color for positive gain/loss', () => {
    const { container } = render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(container.innerHTML).toContain('text-green-600');
  });

  it('applies red color for negative gain/loss', () => {
    const negativePortfolio = { ...mockPortfolio, totalGainLoss: -5000, totalGainLossPercent: -5.0 };
    const { container } = render(<PortfolioSummary portfolio={negativePortfolio} />);
    expect(container.innerHTML).toContain('text-red-600');
  });

  it('shows last updated text', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText(/Last updated/)).toBeInTheDocument();
  });
});
