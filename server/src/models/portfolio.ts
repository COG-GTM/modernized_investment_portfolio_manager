import { z } from "zod";

/**
 * Zod schemas + inferred types ported from the FastAPI Pydantic models in
 * `backend/models/portfolio.py`. Schemas are the single source of truth for
 * both runtime validation and the TypeScript types (matching the
 * Cloudscape-Dashboard convention of Zod-inferred types).
 */

export const portfolioHoldingSchema = z.object({
  symbol: z.string(),
  name: z.string(),
  shares: z.number().int(),
  currentPrice: z.number(),
  marketValue: z.number(),
  gainLoss: z.number(),
  gainLossPercent: z.number(),
});
export type PortfolioHolding = z.infer<typeof portfolioHoldingSchema>;

export const portfolioSummarySchema = z.object({
  accountNumber: z.string(),
  totalValue: z.number(),
  totalGainLoss: z.number(),
  totalGainLossPercent: z.number(),
  holdings: z.array(portfolioHoldingSchema),
  lastUpdated: z.string(),
});
export type PortfolioSummary = z.infer<typeof portfolioSummarySchema>;

export const accountValidationResponseSchema = z.object({
  valid: z.boolean(),
  message: z.string(),
});
export type AccountValidationResponse = z.infer<
  typeof accountValidationResponseSchema
>;

export const portfolioValidationResponseSchema = z.object({
  valid: z.boolean(),
  message: z.string(),
  field: z.string(),
});
export type PortfolioValidationResponse = z.infer<
  typeof portfolioValidationResponseSchema
>;

export const validationErrorResponseSchema = z.object({
  valid: z.boolean(),
  errors: z.array(portfolioValidationResponseSchema),
});
export type ValidationErrorResponse = z.infer<
  typeof validationErrorResponseSchema
>;

export const transactionResponseSchema = z.object({
  accountNumber: z.string(),
  transactions: z.array(z.record(z.string(), z.unknown())),
  message: z.string(),
});
export type TransactionResponse = z.infer<typeof transactionResponseSchema>;
