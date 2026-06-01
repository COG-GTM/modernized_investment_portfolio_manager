import { z } from 'zod';

export const accountNumberSchema = z
  .string()
  .length(10, 'Account number must be exactly 10 digits')
  .regex(/^\d+$/, 'Account number must contain only numeric characters');

export type AccountNumber = z.infer<typeof accountNumberSchema>;

export const accountFormSchema = z.object({
  accountNumber: accountNumberSchema,
});

export type AccountFormData = z.infer<typeof accountFormSchema>;

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

// --- Inquiry API types (BMS map migration) ---

export interface InquiryPosition {
  portfolio_id: string;
  investment_id: string;
  date: string;
  quantity: number;
  cost_basis: number;
  market_value: number;
  currency: string;
  status: string;
  gain_loss: number;
  gain_loss_percent: number;
  last_maint_date: string;
  last_maint_user: string;
}

export interface PortfolioSummaryInfo {
  portfolio_id: string;
  client_name: string;
  total_value: number;
  cash_balance: number;
  status: string;
}

export interface PortfolioInquiryResponse {
  account_number: string;
  positions: InquiryPosition[];
  portfolio_summary: PortfolioSummaryInfo;
  message: string;
}

export interface TransactionRecord {
  date: string;
  time: string;
  type: string;
  investment_id: string;
  quantity: number;
  price: number;
  amount: number;
  status: string;
  sequence_no: string;
}

export interface HistoryInquiryResponse {
  account_number: string;
  transactions: TransactionRecord[];
  message: string;
}

export interface MenuOption {
  code: string;
  label: string;
  description: string;
}

export interface MenuResponse {
  options: MenuOption[];
}
