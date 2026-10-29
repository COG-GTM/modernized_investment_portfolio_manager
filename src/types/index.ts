export interface Position {
  portfolioId: string;
  investmentId: string;
  symbol: string;
  name: string;
  quantity: number;
  costBasis: number;
  currentPrice: number | null;
  marketValue: number | null;
  currency: string;
  status: 'ACTIVE' | 'INACTIVE' | 'PENDING';
  gainLoss: number | null;
  gainLossPercent: number | null;
  lastUpdated: string;
}

export interface Portfolio {
  portfolioId: string;
  accountNumber: string;
  totalValue: number;
  totalCostBasis: number;
  totalGainLoss: number;
  totalGainLossPercent: number;
  currency: string;
  positions: Position[];
  lastUpdated: string;
}

export type { PortfolioHolding, PortfolioSummary, AccountFormData } from './account';
