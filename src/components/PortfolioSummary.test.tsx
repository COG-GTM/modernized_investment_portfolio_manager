import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PortfolioSummary from './PortfolioSummary';
import type { Portfolio } from '../types';

const mockPortfolio: Portfolio = {
  portfolioId: 'PF-001',
  accountNumber: '1234567890',
  totalValue: 50000,
  totalCostBasis: 45000,
  totalGainLoss: 5000,
  totalGainLossPercent: 11.11,
  currency: 'USD',
  positions: [
    {
      portfolioId: 'PF-001',
      investmentId: 'INV-001',
      symbol: 'AAPL',
      name: 'Apple Inc.',
      quantity: 10,
      costBasis: 1500,
      currentPrice: 175,
      marketValue: 1750,
      currency: 'USD',
      status: 'ACTIVE',
      gainLoss: 250,
      gainLossPercent: 16.67,
      lastUpdated: '2024-01-01T00:00:00Z',
    },
  ],
  lastUpdated: '2024-01-15T10:30:00Z',
};

describe('PortfolioSummary', () => {
  it('renders the portfolio summary heading', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('Portfolio Summary')).toBeInTheDocument();
  });

  it('displays the total value', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('$50,000.00')).toBeInTheDocument();
  });

  it('displays the total gain/loss', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('$5,000.00')).toBeInTheDocument();
  });

  it('displays the gain/loss percentage', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('11.11%')).toBeInTheDocument();
  });

  it('displays the account number', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('1234567890')).toBeInTheDocument();
  });

  it('displays the portfolio ID', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('PF-001')).toBeInTheDocument();
  });

  it('displays the number of positions', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('displays the total cost basis', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('$45,000.00')).toBeInTheDocument();
  });

  it('renders the New Search button when onNewSearch is provided', () => {
    const onNewSearch = vi.fn();
    render(<PortfolioSummary portfolio={mockPortfolio} onNewSearch={onNewSearch} />);
    const button = screen.getByText('New Search');
    expect(button).toBeInTheDocument();
  });

  it('calls onNewSearch when the button is clicked', () => {
    const onNewSearch = vi.fn();
    render(<PortfolioSummary portfolio={mockPortfolio} onNewSearch={onNewSearch} />);
    fireEvent.click(screen.getByText('New Search'));
    expect(onNewSearch).toHaveBeenCalledOnce();
  });

  it('does not render the New Search button when onNewSearch is not provided', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.queryByText('New Search')).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <PortfolioSummary portfolio={mockPortfolio} className="custom-class" />
    );
    // The className is applied to the Card wrapper
    expect(container.innerHTML).toContain('custom-class');
  });

  it('renders with negative gain/loss', () => {
    const lossPortfolio: Portfolio = {
      ...mockPortfolio,
      totalGainLoss: -3000,
      totalGainLossPercent: -6.0,
    };
    render(<PortfolioSummary portfolio={lossPortfolio} />);
    expect(screen.getByText('-$3,000.00')).toBeInTheDocument();
  });
});
