import { z } from 'zod';

export const accountNumberSchema = z
  .string()
  .length(10, 'Account number must be exactly 10 digits')
  .regex(/^\d+$/, 'Account number must contain only numeric characters')
  .refine(
    (value) => !value.includes('0'),
    'Account number cannot contain zero digits'
  );

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
