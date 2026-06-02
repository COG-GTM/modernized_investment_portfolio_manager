import { and, asc, eq } from "drizzle-orm";
import type { Database } from "./types.js";
import {
  portfolios,
  positions,
  transactions,
  history,
  type PortfolioRow,
  type PositionRow,
  type TransactionRow,
  type HistoryRow,
} from "../db/schema.js";
import { calculateGainLoss, positionToDict } from "../models/position.js";
import { transactionToDict } from "../models/transaction.js";
import { historyToDict } from "../models/history.js";
import { toDecimal, toNumber } from "../models/decimal.js";

/**
 * Data-access (repository) functions backed by Drizzle. These expose clean,
 * importable read/write helpers so the API/routes layer (migrated separately)
 * can wire the DB layer in without duplicating query logic.
 */

export async function getPortfolioByAccount(
  db: Database,
  accountNo: string,
): Promise<PortfolioRow | undefined> {
  const [row] = await db
    .select()
    .from(portfolios)
    .where(eq(portfolios.accountNo, accountNo))
    .limit(1);
  return row;
}

export async function getPortfolioByPortId(
  db: Database,
  portId: string,
): Promise<PortfolioRow | undefined> {
  const [row] = await db
    .select()
    .from(portfolios)
    .where(eq(portfolios.portId, portId))
    .limit(1);
  return row;
}

export async function getPositions(
  db: Database,
  portfolioId: string,
): Promise<PositionRow[]> {
  return db
    .select()
    .from(positions)
    .where(eq(positions.portfolioId, portfolioId))
    .orderBy(asc(positions.investmentId));
}

export async function getActivePositions(
  db: Database,
  portfolioId: string,
): Promise<PositionRow[]> {
  return db
    .select()
    .from(positions)
    .where(and(eq(positions.portfolioId, portfolioId), eq(positions.status, "A")))
    .orderBy(asc(positions.investmentId));
}

export async function getTransactions(
  db: Database,
  portfolioId: string,
): Promise<TransactionRow[]> {
  return db
    .select()
    .from(transactions)
    .where(eq(transactions.portfolioId, portfolioId))
    .orderBy(asc(transactions.date), asc(transactions.time));
}

export async function getHistory(
  db: Database,
  portfolioId: string,
): Promise<HistoryRow[]> {
  return db
    .select()
    .from(history)
    .where(eq(history.portfolioId, portfolioId))
    .orderBy(asc(history.date), asc(history.time), asc(history.seqNo));
}

export interface PortfolioHoldingView {
  symbol: string;
  shares: number;
  currentPrice: number;
  marketValue: number;
  costBasis: number;
  gainLoss: number;
  gainLossPercent: number;
}

export interface PortfolioSummaryView {
  accountNumber: string;
  portfolioId: string;
  totalValue: number;
  cashBalance: number;
  totalGainLoss: number;
  totalGainLossPercent: number;
  holdings: PortfolioHoldingView[];
}

/**
 * Build a portfolio summary (account totals + holdings) directly from the DB.
 * Aggregates active positions, mirroring the shape the frontend/routes consume.
 */
export async function getPortfolioSummary(
  db: Database,
  accountNo: string,
): Promise<PortfolioSummaryView | undefined> {
  const portfolio = await getPortfolioByAccount(db, accountNo);
  if (!portfolio) return undefined;

  const activePositions = await getActivePositions(db, portfolio.portId);

  let totalCost = toDecimal(0);
  let totalMarket = toDecimal(0);

  const holdings: PortfolioHoldingView[] = activePositions.map((pos) => {
    const gl = calculateGainLoss(pos);
    const shares = toDecimal(pos.quantity);
    const marketValue = toDecimal(pos.marketValue);
    const costBasis = toDecimal(pos.costBasis);
    totalCost = totalCost.plus(costBasis);
    totalMarket = totalMarket.plus(marketValue);

    const currentPrice = shares.isZero()
      ? 0
      : marketValue.dividedBy(shares).toNumber();

    return {
      symbol: pos.investmentId,
      shares: shares.toNumber(),
      currentPrice,
      marketValue: marketValue.toNumber(),
      costBasis: costBasis.toNumber(),
      gainLoss: gl.gain_loss.toNumber(),
      gainLossPercent: gl.gain_loss_percent.toNumber(),
    };
  });

  const totalGainLoss = totalMarket.minus(totalCost);
  const totalGainLossPercent = totalCost.isZero()
    ? 0
    : totalGainLoss.dividedBy(totalCost).times(100).toNumber();

  return {
    accountNumber: accountNo,
    portfolioId: portfolio.portId,
    totalValue: toNumber(portfolio.totalValue),
    cashBalance: toNumber(portfolio.cashBalance),
    totalGainLoss: totalGainLoss.toNumber(),
    totalGainLossPercent,
    holdings,
  };
}

export {
  positionToDict,
  transactionToDict,
  historyToDict,
};
