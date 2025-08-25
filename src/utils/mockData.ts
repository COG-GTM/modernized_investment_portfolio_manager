import type { PortfolioSummary } from '../types/account';

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
