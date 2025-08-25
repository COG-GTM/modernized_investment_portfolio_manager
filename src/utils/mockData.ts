import type { PortfolioSummary } from '../types/account';
import type { Portfolio, Position } from '../types';

export function generateMockPortfolio(accountNumber: string): PortfolioSummary {
  return {
    accountNumber,
    totalValue: 125750.50,
    totalGainLoss: 8250.50,
    totalGainLossPercent: 7.02,
    lastUpdated: new Date().toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
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
      {
        symbol: 'MSFT',
        name: 'Microsoft Corporation',
        shares: 100,
        currentPrice: 378.85,
        marketValue: 37885.00,
        gainLoss: 3885.00,
        gainLossPercent: 11.42,
      },
      {
        symbol: 'GOOGL',
        name: 'Alphabet Inc.',
        shares: 75,
        currentPrice: 142.56,
        marketValue: 10692.00,
        gainLoss: 692.00,
        gainLossPercent: 6.92,
      },
      {
        symbol: 'TSLA',
        name: 'Tesla Inc.',
        shares: 200,
        currentPrice: 245.67,
        marketValue: 49134.00,
        gainLoss: 1386.00,
        gainLossPercent: 2.90,
      },
    ],
  };
}

export function generateMockPortfolioEnhanced(accountNumber: string): Portfolio {
  const positions: Position[] = [
    {
      portfolioId: `PF-${accountNumber}`,
      investmentId: 'INV-AAPL-001',
      symbol: 'AAPL',
      name: 'Apple Inc.',
      quantity: 150,
      costBasis: 25500.00,
      currentPrice: 185.25,
      marketValue: 27787.50,
      currency: 'USD',
      status: 'ACTIVE',
      gainLoss: 2287.50,
      gainLossPercent: 8.97,
      lastUpdated: new Date().toISOString(),
    },
    {
      portfolioId: `PF-${accountNumber}`,
      investmentId: 'INV-MSFT-001',
      symbol: 'MSFT',
      name: 'Microsoft Corporation',
      quantity: 100,
      costBasis: 34000.00,
      currentPrice: 378.85,
      marketValue: 37885.00,
      currency: 'USD',
      status: 'ACTIVE',
      gainLoss: 3885.00,
      gainLossPercent: 11.42,
      lastUpdated: new Date().toISOString(),
    },
    {
      portfolioId: `PF-${accountNumber}`,
      investmentId: 'INV-GOOGL-001',
      symbol: 'GOOGL',
      name: 'Alphabet Inc.',
      quantity: 75,
      costBasis: 10000.00,
      currentPrice: 142.56,
      marketValue: 10692.00,
      currency: 'USD',
      status: 'ACTIVE',
      gainLoss: 692.00,
      gainLossPercent: 6.92,
      lastUpdated: new Date().toISOString(),
    },
    {
      portfolioId: `PF-${accountNumber}`,
      investmentId: 'INV-TSLA-001',
      symbol: 'TSLA',
      name: 'Tesla Inc.',
      quantity: 200,
      costBasis: 47748.00,
      currentPrice: 245.67,
      marketValue: 49134.00,
      currency: 'USD',
      status: 'ACTIVE',
      gainLoss: 1386.00,
      gainLossPercent: 2.90,
      lastUpdated: new Date().toISOString(),
    },
  ];

  const totalCostBasis = positions.reduce((sum, pos) => sum + pos.costBasis, 0);
  const totalValue = positions.reduce((sum, pos) => sum + pos.marketValue, 0);
  const totalGainLoss = totalValue - totalCostBasis;

  return {
    portfolioId: `PF-${accountNumber}`,
    accountNumber,
    totalValue,
    totalCostBasis,
    totalGainLoss,
    totalGainLossPercent: (totalGainLoss / totalCostBasis) * 100,
    currency: 'USD',
    positions,
    lastUpdated: new Date().toISOString(),
  };
}
