import { z } from 'zod';

export const inquiryAccountSchema = z
  .string()
  .length(10, 'Account number must be exactly 10 digits')
  .regex(/^\d+$/, 'Account number must contain only numeric characters');

export const inquiryFormSchema = z.object({
  accountNumber: inquiryAccountSchema,
});

export type InquiryFormData = z.infer<typeof inquiryFormSchema>;

export type InquiryTab = 'portfolio' | 'history';

export interface PositionDetail {
  portfolioId: string;
  investmentId: string;
  positionDate: string | null;
  quantity: number;
  costBasis: number;
  marketValue: number;
  currency: string;
  status: string;
  gainLoss: number;
  gainLossPercent: number;
  lastMaintDate: string | null;
  lastMaintUser: string | null;
}

export interface PortfolioInquiryResult {
  accountNumber: string;
  portfolioId: string;
  portfolioName: string | null;
  clientName: string | null;
  clientType: string | null;
  status: string | null;
  totalValue: number;
  totalCostBasis: number;
  totalGainLoss: number;
  totalGainLossPercent: number;
  cashBalance: number;
  currency: string;
  positions: PositionDetail[];
  lastUpdated: string;
}

export interface HistoryEntry {
  transactionDate: string | null;
  transactionType: string;
  quantity: number;
  price: number;
  amount: number;
  investmentId: string | null;
  status: string | null;
}

export interface TransactionHistoryResult {
  accountNumber: string;
  portfolioId: string;
  entries: HistoryEntry[];
  totalEntries: number;
  hasMore: boolean;
  message: string;
}
