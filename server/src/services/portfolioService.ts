import { and, eq } from "drizzle-orm";
import type { Database } from "./types.js";
import {
  portfolios,
  positions,
  transactions,
  history,
  type PositionRow,
  type TransactionRow,
} from "../db/schema.js";
import { calculateTotalValue, portfolioToDict } from "../models/portfolio.js";
import { positionToDict } from "../models/position.js";
import {
  transactionToDict,
  transitionStatus,
  validateTransaction,
} from "../models/transaction.js";
import { createAuditRecord } from "../models/history.js";
import { Decimal, toDecimal } from "../models/decimal.js";

export interface ProcessResult {
  success: boolean;
  errors: string[];
}

function todayDateString(): string {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

/**
 * Portfolio transaction-processing service ported from
 * `backend/services/portfolio_service.py` (class `PortfolioService`).
 *
 * Uses a Drizzle transaction to mirror the SQLAlchemy commit/rollback
 * semantics of the original implementation.
 */
export class PortfolioService {
  constructor(private readonly db: Database) {}

  async processTransaction(transaction: TransactionRow): Promise<ProcessResult> {
    const validation = validateTransaction(transaction);
    if (!validation.valid) {
      return { success: false, errors: validation.errors };
    }

    try {
      await this.db.transaction(async (tx) => {
        const auditRecord = await createAuditRecord({
          portfolioId: transaction.portfolioId,
          recordType: "TR",
          actionCode: "A",
          afterData: transactionToDict(transaction),
          reasonCode: "PROC",
          user: transaction.processUser ?? "SYSTEM",
          db: tx,
        });
        await tx.insert(history).values(auditRecord);

        if (transaction.type === "BU" || transaction.type === "SL") {
          await this.processBuySellTransaction(tx, transaction);
        } else if (transaction.type === "TR") {
          await this.processTransferTransaction(tx, transaction);
        } else if (transaction.type === "FE") {
          await this.processFeeTransaction(tx, transaction);
        }

        if (!transitionStatus(transaction, "D", transaction.processUser ?? "SYSTEM")) {
          throw new Error(
            `Invalid status transition to 'D' from '${transaction.status}'`,
          );
        }
        await this.persistTransactionStatus(tx, transaction);

        await this.updatePortfolioTotalValue(tx, transaction.portfolioId);
      });

      return { success: true, errors: [] };
    } catch (err) {
      transitionStatus(transaction, "F", transaction.processUser ?? "SYSTEM");
      return { success: false, errors: [(err as Error).message] };
    }
  }

  private async processBuySellTransaction(
    tx: Database,
    transaction: TransactionRow,
  ): Promise<void> {
    const [existing] = await tx
      .select()
      .from(positions)
      .where(
        and(
          eq(positions.portfolioId, transaction.portfolioId),
          eq(positions.investmentId, transaction.investmentId ?? ""),
          eq(positions.date, transaction.date),
        ),
      )
      .limit(1);

    const isNew = !existing;
    const position: PositionRow =
      existing ??
      ({
        portfolioId: transaction.portfolioId,
        date: transaction.date,
        investmentId: transaction.investmentId ?? "",
        quantity: "0.0000",
        costBasis: "0.00",
        marketValue: "0.00",
        currency: transaction.currency,
        status: "A",
        lastMaintDate: new Date(),
        lastMaintUser: transaction.processUser,
      } as PositionRow);

    const originalQty = toDecimal(position.quantity);
    const beforeData =
      position.quantity && !originalQty.isZero() ? positionToDict(position) : null;

    const txQty = toDecimal(transaction.quantity);
    const txAmount = toDecimal(transaction.amount);

    if (transaction.type === "BU") {
      position.quantity = originalQty.plus(txQty).toFixed(4);
      position.costBasis = toDecimal(position.costBasis).plus(txAmount).toFixed(2);
    } else if (transaction.type === "SL") {
      const newQuantity = originalQty.minus(txQty);
      if (position.quantity && originalQty.greaterThan(0)) {
        const costPerShare = toDecimal(position.costBasis).dividedBy(originalQty);
        const costReduction = txQty.times(costPerShare);
        position.costBasis = toDecimal(position.costBasis)
          .minus(costReduction)
          .toFixed(2);
      }
      position.quantity = newQuantity.toFixed(4);
    }

    position.lastMaintDate = new Date();
    position.lastMaintUser = transaction.processUser;

    if (isNew) {
      await tx.insert(positions).values(position);
    } else {
      await tx
        .update(positions)
        .set({
          quantity: position.quantity,
          costBasis: position.costBasis,
          lastMaintDate: position.lastMaintDate,
          lastMaintUser: position.lastMaintUser,
        })
        .where(
          and(
            eq(positions.portfolioId, position.portfolioId),
            eq(positions.investmentId, position.investmentId),
            eq(positions.date, position.date),
          ),
        );
    }

    const auditRecord = await createAuditRecord({
      portfolioId: transaction.portfolioId,
      recordType: "PS",
      actionCode: "C",
      beforeData,
      afterData: positionToDict(position),
      reasonCode: "TRAN",
      user: transaction.processUser ?? "SYSTEM",
      db: tx,
    });
    await tx.insert(history).values(auditRecord);
  }

  // Transfer transactions are a no-op in the original implementation.
  private async processTransferTransaction(
    _tx: Database,
    _transaction: TransactionRow,
  ): Promise<void> {
    // Intentionally left as a placeholder, mirroring the Python service.
  }

  private async processFeeTransaction(
    tx: Database,
    transaction: TransactionRow,
  ): Promise<void> {
    const [portfolio] = await tx
      .select()
      .from(portfolios)
      .where(eq(portfolios.portId, transaction.portfolioId))
      .limit(1);

    if (!portfolio) return;

    const beforeData = portfolioToDict(portfolio);
    const newCashBalance = toDecimal(portfolio.cashBalance)
      .minus(toDecimal(transaction.amount))
      .toFixed(2);

    portfolio.cashBalance = newCashBalance;
    portfolio.lastMaint = todayDateString();
    portfolio.lastUser = transaction.processUser;

    await tx
      .update(portfolios)
      .set({
        cashBalance: portfolio.cashBalance,
        lastMaint: portfolio.lastMaint,
        lastUser: portfolio.lastUser,
      })
      .where(eq(portfolios.portId, transaction.portfolioId));

    const auditRecord = await createAuditRecord({
      portfolioId: transaction.portfolioId,
      recordType: "PT",
      actionCode: "C",
      beforeData,
      afterData: portfolioToDict(portfolio),
      reasonCode: "FEE",
      user: transaction.processUser ?? "SYSTEM",
      db: tx,
    });
    await tx.insert(history).values(auditRecord);
  }

  /**
   * Persist the transaction's status/process fields back to the `transactions`
   * row. In the Python service the `transaction` is a session-attached object,
   * so the final `db.commit()` durably stores the `'D'` status; here we issue an
   * explicit UPDATE (by primary key) inside the same Drizzle transaction so a
   * processed transaction cannot be re-selected as pending and reprocessed.
   */
  private async persistTransactionStatus(
    tx: Database,
    transaction: TransactionRow,
  ): Promise<void> {
    await tx
      .update(transactions)
      .set({
        status: transaction.status,
        processDate: transaction.processDate,
        processUser: transaction.processUser,
      })
      .where(
        and(
          eq(transactions.date, transaction.date),
          eq(transactions.time, transaction.time),
          eq(transactions.portfolioId, transaction.portfolioId),
          eq(transactions.sequenceNo, transaction.sequenceNo),
        ),
      );
  }

  /** Recompute and persist a portfolio's total value. Mirrors `Portfolio.update_total_value`. */
  private async updatePortfolioTotalValue(
    tx: Database,
    portfolioId: string,
  ): Promise<void> {
    const [portfolio] = await tx
      .select()
      .from(portfolios)
      .where(eq(portfolios.portId, portfolioId))
      .limit(1);

    if (!portfolio) return;

    const portfolioPositions = await tx
      .select()
      .from(positions)
      .where(eq(positions.portfolioId, portfolioId));

    const total: Decimal = calculateTotalValue(portfolio, portfolioPositions);

    await tx
      .update(portfolios)
      .set({ totalValue: total.toFixed(2), lastMaint: todayDateString() })
      .where(eq(portfolios.portId, portfolioId));
  }
}
