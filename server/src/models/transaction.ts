import type { TransactionRow } from "../db/schema.js";
import { Decimal, toDecimal, toNumber } from "./decimal.js";
import type { ValidationResult } from "./portfolio.js";

/**
 * Transaction model logic ported from `backend/models/transactions.py`
 * (class `Transaction`).
 */

export const VALID_STATUS_TRANSITIONS: Record<string, string[]> = {
  P: ["D", "F"],
  D: ["R"],
  F: ["P"],
  R: [],
};

export interface TransactionDict {
  date: string | null;
  time: string | null;
  portfolio_id: string;
  sequence_no: string;
  investment_id: string | null;
  type: string | null;
  quantity: number;
  price: number;
  amount: number;
  currency: string | null;
  status: string | null;
  process_date: string | null;
  process_user: string | null;
}

export function validateTransaction(t: Partial<TransactionRow>): ValidationResult {
  const errors: string[] = [];

  if (!t.portfolioId || t.portfolioId.length !== 8) {
    errors.push("Portfolio ID must be 8 characters");
  }

  if (!t.sequenceNo || t.sequenceNo.length !== 6) {
    errors.push("Sequence number must be 6 characters");
  }

  if (!t.type || !["BU", "SL", "TR", "FE"].includes(t.type)) {
    errors.push("Invalid transaction type");
  }

  if (!t.status || !["P", "D", "F", "R"].includes(t.status)) {
    errors.push("Invalid status");
  }

  if (t.type && ["BU", "SL"].includes(t.type) && !t.investmentId) {
    errors.push("Investment ID required for buy/sell transactions");
  }

  if (
    t.type &&
    ["BU", "SL"].includes(t.type) &&
    (!t.quantity || toDecimal(t.quantity).lessThanOrEqualTo(0))
  ) {
    errors.push("Positive quantity required for buy/sell transactions");
  }

  if (
    t.type &&
    ["BU", "SL"].includes(t.type) &&
    (!t.price || toDecimal(t.price).lessThanOrEqualTo(0))
  ) {
    errors.push("Positive price required for buy/sell transactions");
  }

  return { valid: errors.length === 0, errors };
}

export function canTransitionTo(currentStatus: string | null, newStatus: string): boolean {
  if (!currentStatus) return false;
  return (VALID_STATUS_TRANSITIONS[currentStatus] ?? []).includes(newStatus);
}

/**
 * Mutates the transaction row in place, mirroring
 * `Transaction.transition_status`. Returns whether the transition was applied.
 */
export function transitionStatus(
  t: TransactionRow,
  newStatus: string,
  user: string,
): boolean {
  if (!canTransitionTo(t.status, newStatus)) {
    return false;
  }
  t.status = newStatus;
  t.processDate = new Date();
  t.processUser = user;
  return true;
}

export function calculateTransactionAmount(
  t: Pick<TransactionRow, "quantity" | "price">,
): Decimal {
  if (t.quantity && t.price) {
    return toDecimal(t.quantity).times(toDecimal(t.price));
  }
  return new Decimal(0);
}

export function transactionToDict(t: TransactionRow): TransactionDict {
  return {
    date: t.date ?? null,
    time: t.time ?? null,
    portfolio_id: t.portfolioId,
    sequence_no: t.sequenceNo,
    investment_id: t.investmentId ?? null,
    type: t.type ?? null,
    quantity: toNumber(t.quantity),
    price: toNumber(t.price),
    amount: toNumber(t.amount),
    currency: t.currency ?? null,
    status: t.status ?? null,
    process_date: t.processDate ? t.processDate.toISOString() : null,
    process_user: t.processUser ?? null,
  };
}
