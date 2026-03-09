import { z } from 'zod';

export const accountNumberSchema = z
  .string()
  .min(1, 'Account number is required')
  .length(9, 'Account number must be exactly 9 digits')
  .regex(/^\d+$/, 'Account number must contain only digits')
  .refine(val => val !== '000000000', { message: 'Invalid account number' });

export type AccountNumber = z.infer<typeof accountNumberSchema>;

export const accountFormSchema = z.object({
  accountNumber: accountNumberSchema,
});

export type AccountFormData = z.infer<typeof accountFormSchema>;

export const formatAccountNumber = (value: string): string => {
  if (!value) return '';
  const cleaned = value.replace(/\D/g, '');
  if (cleaned.length <= 3) return cleaned;
  if (cleaned.length <= 6) return `${cleaned.slice(0, 3)}-${cleaned.slice(3)}`;
  return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 6)}-${cleaned.slice(6, 9)}`;
};

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
