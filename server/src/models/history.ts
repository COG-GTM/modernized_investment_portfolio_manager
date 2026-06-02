import { and, eq, sql } from "drizzle-orm";
import type { Database } from "../services/types.js";
import { history } from "../db/schema.js";
import type { HistoryInsert, HistoryRow } from "../db/schema.js";

/**
 * History (audit trail) model logic ported from `backend/models/history.py`
 * (class `History`).
 *
 * Note: the SQLAlchemy model declared `time = String(8)`, but the applied
 * Alembic migration created `history.time` as `String(6)`. The Drizzle schema
 * follows the migration (the resulting schema), so the generated audit
 * timestamp uses `HHMMSS` (6 chars) to fit the PostgreSQL column.
 */

export interface HistoryDict {
  portfolio_id: string;
  date: string;
  time: string;
  seq_no: string;
  record_type: string | null;
  action_code: string | null;
  before_data: Record<string, unknown> | null;
  after_data: Record<string, unknown> | null;
  reason_code: string | null;
  process_date: string | null;
  process_user: string | null;
}

/** A serializable audit payload (a model `*Dict` object or plain record). */
export type AuditData = Record<string, unknown> | object;

export interface CreateAuditRecordParams {
  portfolioId: string;
  recordType: string;
  actionCode: string;
  beforeData?: AuditData | null;
  afterData?: AuditData | null;
  reasonCode?: string;
  user?: string;
  db?: Database;
}

function pad(n: number, width: number): string {
  return String(n).padStart(width, "0");
}

/**
 * Build a History audit record. Mirrors `History.create_audit_record`.
 * When a `db` handle is provided, the sequence number is derived from the count
 * of existing records sharing the same (portfolio_id, date, time) key.
 */
export async function createAuditRecord(
  params: CreateAuditRecordParams,
): Promise<HistoryInsert> {
  const {
    portfolioId,
    recordType,
    actionCode,
    beforeData = null,
    afterData = null,
    reasonCode = "AUTO",
    user = "SYSTEM",
    db,
  } = params;

  const now = new Date();
  const dateStr = `${now.getFullYear()}${pad(now.getMonth() + 1, 2)}${pad(now.getDate(), 2)}`;
  const timeStr = `${pad(now.getHours(), 2)}${pad(now.getMinutes(), 2)}${pad(now.getSeconds(), 2)}`;

  let seqNo = "0001";
  if (db) {
    const [row] = await db
      .select({ count: sql<number>`count(*)` })
      .from(history)
      .where(
        and(
          eq(history.portfolioId, portfolioId),
          eq(history.date, dateStr),
          eq(history.time, timeStr),
        ),
      );
    const existingCount = Number(row?.count ?? 0);
    seqNo = pad(existingCount + 1, 4);
  }

  return {
    portfolioId,
    date: dateStr,
    time: timeStr,
    seqNo,
    recordType,
    actionCode,
    beforeImage: beforeData ? JSON.stringify(beforeData) : null,
    afterImage: afterData ? JSON.stringify(afterData) : null,
    reasonCode,
    processDate: now,
    processUser: user,
  };
}

export function getBeforeData(h: Pick<HistoryRow, "beforeImage">): Record<string, unknown> | null {
  if (!h.beforeImage) return null;
  try {
    return JSON.parse(h.beforeImage) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export function getAfterData(h: Pick<HistoryRow, "afterImage">): Record<string, unknown> | null {
  if (!h.afterImage) return null;
  try {
    return JSON.parse(h.afterImage) as Record<string, unknown>;
  } catch {
    return null;
  }
}

export function historyToDict(h: HistoryRow): HistoryDict {
  return {
    portfolio_id: h.portfolioId,
    date: h.date,
    time: h.time,
    seq_no: h.seqNo,
    record_type: h.recordType ?? null,
    action_code: h.actionCode ?? null,
    before_data: getBeforeData(h),
    after_data: getAfterData(h),
    reason_code: h.reasonCode ?? null,
    process_date: h.processDate ? h.processDate.toISOString() : null,
    process_user: h.processUser ?? null,
  };
}
