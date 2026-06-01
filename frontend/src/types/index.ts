export interface Position {
  portfolioId: string;
  investmentId: string;
  symbol: string;
  name: string;
  quantity: number;
  costBasis: number;
  currentPrice: number;
  marketValue: number;
  currency: string;
  status: 'ACTIVE' | 'INACTIVE' | 'PENDING';
  gainLoss: number;
  gainLossPercent: number;
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

export interface PortfolioHolding {
  symbol: string;
  name: string;
  shares: number;
  currentPrice: number;
  marketValue: number;
  gainLoss: number;
  gainLossPercent: number;
}

export interface PortfolioSummary {
  accountNumber: string;
  totalValue: number;
  totalGainLoss: number;
  totalGainLossPercent: number;
  holdings: PortfolioHolding[];
  lastUpdated: string;
}

export interface Transaction {
  date: string;
  type: string;
  units: number;
  price: number;
  amount: number;
  fundId?: string;
  transactionId?: string;
}

export interface TransactionHistoryResponse {
  accountNumber: string;
  transactions: Transaction[];
  message: string;
  currentPage: number;
  totalPages: number;
  totalItems: number;
}

export interface AuthUser {
  username: string;
  token: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  username: string;
}
