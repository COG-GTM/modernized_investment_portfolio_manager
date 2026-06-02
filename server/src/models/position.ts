import type { PositionRow } from "../db/schema.js";
import { Decimal, toDecimal, toNumber } from "./decimal.js";
import type { ValidationResult } from "./portfolio.js";

/**
 * Position model logic ported from `backend/models/database.py` (class
 * `Position`).
 */

export interface GainLoss {
  gain_loss: Decimal;
  gain_loss_percent: Decimal;
}

export interface PositionDict {
  portfolio_id: string;
  date: string | null;
  investment_id: string;
  quantity: number;
  cost_basis: number;
  market_value: number;
  currency: string | null;
  status: string | null;
  gain_loss: number;
  gain_loss_percent: number;
  last_maint_date: string | null;
  last_maint_user: string | null;
}

export function calculateGainLoss(
  p: Pick<PositionRow, "costBasis" | "marketValue">,
): GainLoss {
  const costBasis = toDecimal(p.costBasis);
  const marketValue = toDecimal(p.marketValue);

  if (!p.costBasis || !p.marketValue) {
    return { gain_loss: new Decimal(0), gain_loss_percent: new Decimal(0) };
  }

  const gainLoss = marketValue.minus(costBasis);
  const gainLossPercent = costBasis.isZero()
    ? new Decimal(0)
    : gainLoss.dividedBy(costBasis).times(100);

  return { gain_loss: gainLoss, gain_loss_percent: gainLossPercent };
}

export function validatePosition(p: Partial<PositionRow>): ValidationResult {
  const errors: string[] = [];

  if (!p.portfolioId || p.portfolioId.length !== 8) {
    errors.push("Portfolio ID must be 8 characters");
  }

  if (!p.investmentId || p.investmentId.length !== 10) {
    errors.push("Investment ID must be 10 characters");
  }

  if (!p.status || !["A", "C", "P"].includes(p.status)) {
    errors.push("Invalid status");
  }

  if (p.quantity && toDecimal(p.quantity).isNegative()) {
    errors.push("Quantity cannot be negative");
  }

  return { valid: errors.length === 0, errors };
}

export function positionToDict(p: PositionRow): PositionDict {
  const gainLoss = calculateGainLoss(p);
  return {
    portfolio_id: p.portfolioId,
    date: p.date ?? null,
    investment_id: p.investmentId,
    quantity: toNumber(p.quantity),
    cost_basis: toNumber(p.costBasis),
    market_value: toNumber(p.marketValue),
    currency: p.currency ?? null,
    status: p.status ?? null,
    gain_loss: gainLoss.gain_loss.toNumber(),
    gain_loss_percent: gainLoss.gain_loss_percent.toNumber(),
    last_maint_date: p.lastMaintDate ? p.lastMaintDate.toISOString() : null,
    last_maint_user: p.lastMaintUser ?? null,
  };
}
