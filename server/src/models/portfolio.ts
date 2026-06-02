import type { PortfolioRow, PositionRow } from "../db/schema.js";
import { Decimal, toDecimal, toNumber } from "./decimal.js";

/**
 * Portfolio model logic ported from `backend/models/database.py` (class
 * `Portfolio`). Implemented as pure functions over Drizzle row objects.
 */

export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

export interface PortfolioDict {
  port_id: string;
  account_no: string;
  client_name: string | null;
  client_type: string | null;
  create_date: string | null;
  last_maint: string | null;
  status: string | null;
  total_value: number;
  cash_balance: number;
  last_user: string | null;
  last_trans: string | null;
}

export function validatePortfolio(p: Partial<PortfolioRow>): ValidationResult {
  const errors: string[] = [];

  if (!p.portId || p.portId.length !== 8) {
    errors.push("Portfolio ID must be 8 characters");
  }

  if (!p.accountNo || p.accountNo.length !== 10) {
    errors.push("Account number must be 10 characters");
  }

  if (!p.clientType || !["I", "C", "T"].includes(p.clientType)) {
    errors.push("Invalid client type");
  }

  if (!p.status || !["A", "C", "S"].includes(p.status)) {
    errors.push("Invalid status");
  }

  return { valid: errors.length === 0, errors };
}

/**
 * Sum of active positions' market value plus the portfolio cash balance.
 * Mirrors `Portfolio.calculate_total_value`.
 */
export function calculateTotalValue(
  portfolio: Pick<PortfolioRow, "cashBalance">,
  positions: Pick<PositionRow, "marketValue" | "status">[],
): Decimal {
  let total = new Decimal(0);
  for (const position of positions) {
    if (position.status === "A") {
      total = total.plus(toDecimal(position.marketValue));
    }
  }
  total = total.plus(toDecimal(portfolio.cashBalance));
  return total;
}

export function portfolioToDict(p: PortfolioRow): PortfolioDict {
  return {
    port_id: p.portId,
    account_no: p.accountNo,
    client_name: p.clientName ?? null,
    client_type: p.clientType ?? null,
    create_date: p.createDate ?? null,
    last_maint: p.lastMaint ?? null,
    status: p.status ?? null,
    total_value: toNumber(p.totalValue),
    cash_balance: toNumber(p.cashBalance),
    last_user: p.lastUser ?? null,
    last_trans: p.lastTrans ?? null,
  };
}
