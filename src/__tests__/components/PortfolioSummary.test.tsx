import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PortfolioSummary from '../../components/PortfolioSummary';
import type { Portfolio } from '../../types';

const mockPortfolio: Portfolio = {
  portfolioId: 'PF-12345',
  accountNumber: '1234567890',
  totalValue: 125000.50,
  totalCostBasis: 117000.00,
  totalGainLoss: 8000.50,
  totalGainLossPercent: 6.84,
  currency: 'USD',
  positions: [
    {
      portfolioId: 'PF-12345',
      investmentId: 'INV-AAPL-001',
      symbol: 'AAPL',
      name: 'Apple Inc.',
      quantity: 100,
      costBasis: 15000,
      currentPrice: 185.25,
      marketValue: 18525,
      currency: 'USD',
      status: 'ACTIVE',
      gainLoss: 3525,
      gainLossPercent: 23.5,
      lastUpdated: 'June 10, 2024',
    },
  ],
  lastUpdated: 'June 10, 2024',
};

describe('PortfolioSummary', () => {
  it('renders portfolio summary heading', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('Portfolio Summary')).toBeInTheDocument();
  });

  it('displays total value', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('Total Value')).toBeInTheDocument();
    expect(screen.getByText('$125,000.50')).toBeInTheDocument();
  });

  it('displays total gain/loss', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('Total Gain/Loss')).toBeInTheDocument();
    expect(screen.getByText('$8,000.50')).toBeInTheDocument();
  });

  it('displays gain/loss percentage', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('Gain/Loss %')).toBeInTheDocument();
    expect(screen.getByText('6.84%')).toBeInTheDocument();
  });

  it('displays portfolio ID', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('PF-12345')).toBeInTheDocument();
  });

  it('displays account number', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('1234567890')).toBeInTheDocument();
  });

  it('displays positions count', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('shows New Search button when onNewSearch provided', () => {
    const onNewSearch = vi.fn();
    render(<PortfolioSummary portfolio={mockPortfolio} onNewSearch={onNewSearch} />);
    const btn = screen.getByText('New Search');
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(onNewSearch).toHaveBeenCalledTimes(1);
  });

  it('hides New Search button when onNewSearch not provided', () => {
    render(<PortfolioSummary portfolio={mockPortfolio} />);
    expect(screen.queryByText('New Search')).not.toBeInTheDocument();
  });
});
