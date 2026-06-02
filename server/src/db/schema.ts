import { sql } from "drizzle-orm";
import {
  pgTable,
  varchar,
  numeric,
  date,
  time,
  timestamp,
  text,
  index,
  primaryKey,
  unique,
  check,
  foreignKey,
} from "drizzle-orm/pg-core";

/**
 * Drizzle schema ported from the SQLAlchemy models in
 * `backend/models/*.py`. Column names, types, lengths, primary keys,
 * check constraints, foreign keys and indexes mirror the original
 * Alembic-generated schema.
 *
 * Note on foreign keys: the SQLAlchemy models declared FKs that reference
 * `portfolios.port_id` alone, while `portfolios` has a composite primary key
 * (`port_id`, `account_no`). SQLite tolerated this, but PostgreSQL requires
 * the referenced column to carry a unique constraint, so a UNIQUE constraint
 * is added on `portfolios.port_id` to preserve the referential relationship.
 */

export const portfolios = pgTable(
  "portfolios",
  {
    portId: varchar("port_id", { length: 8 }).notNull(),
    accountNo: varchar("account_no", { length: 10 }).notNull(),

    clientName: varchar("client_name", { length: 30 }),
    clientType: varchar("client_type", { length: 1 }),

    createDate: date("create_date"),
    lastMaint: date("last_maint"),
    status: varchar("status", { length: 1 }),

    totalValue: numeric("total_value", { precision: 15, scale: 2 }),
    cashBalance: numeric("cash_balance", { precision: 15, scale: 2 }),

    lastUser: varchar("last_user", { length: 8 }),
    lastTrans: varchar("last_trans", { length: 8 }),
  },
  (t) => [
    primaryKey({ columns: [t.portId, t.accountNo] }),
    unique("uq_portfolio_port_id").on(t.portId),
    check("ck_portfolio_client_type", sql`${t.clientType} IN ('I', 'C', 'T')`),
    check("ck_portfolio_status", sql`${t.status} IN ('A', 'C', 'S')`),
    index("idx_portfolio_status").on(t.status),
    index("idx_portfolio_client_type").on(t.clientType),
  ],
);

export const positions = pgTable(
  "positions",
  {
    portfolioId: varchar("portfolio_id", { length: 8 }).notNull(),
    date: date("date").notNull(),
    investmentId: varchar("investment_id", { length: 10 }).notNull(),

    quantity: numeric("quantity", { precision: 15, scale: 4 }),
    costBasis: numeric("cost_basis", { precision: 15, scale: 2 }),
    marketValue: numeric("market_value", { precision: 15, scale: 2 }),
    currency: varchar("currency", { length: 3 }),
    status: varchar("status", { length: 1 }),

    lastMaintDate: timestamp("last_maint_date"),
    lastMaintUser: varchar("last_maint_user", { length: 8 }),
  },
  (t) => [
    primaryKey({ columns: [t.portfolioId, t.date, t.investmentId] }),
    foreignKey({
      columns: [t.portfolioId],
      foreignColumns: [portfolios.portId],
      name: "fk_position_portfolio",
    }),
    check("ck_position_status", sql`${t.status} IN ('A', 'C', 'P')`),
    index("idx_position_portfolio_id").on(t.portfolioId),
    index("idx_position_date").on(t.date),
    index("idx_position_investment_id").on(t.investmentId),
    index("idx_position_status").on(t.status),
  ],
);

export const transactions = pgTable(
  "transactions",
  {
    date: date("date").notNull(),
    time: time("time").notNull(),
    portfolioId: varchar("portfolio_id", { length: 8 }).notNull(),
    sequenceNo: varchar("sequence_no", { length: 6 }).notNull(),

    investmentId: varchar("investment_id", { length: 10 }),
    type: varchar("type", { length: 2 }),
    quantity: numeric("quantity", { precision: 15, scale: 4 }),
    price: numeric("price", { precision: 15, scale: 4 }),
    amount: numeric("amount", { precision: 15, scale: 2 }),
    currency: varchar("currency", { length: 3 }),
    status: varchar("status", { length: 1 }),

    processDate: timestamp("process_date"),
    processUser: varchar("process_user", { length: 8 }),
  },
  (t) => [
    primaryKey({ columns: [t.date, t.time, t.portfolioId, t.sequenceNo] }),
    foreignKey({
      columns: [t.portfolioId],
      foreignColumns: [portfolios.portId],
      name: "fk_transaction_portfolio",
    }),
    check("ck_transaction_type", sql`${t.type} IN ('BU', 'SL', 'TR', 'FE')`),
    check("ck_transaction_status", sql`${t.status} IN ('P', 'D', 'F', 'R')`),
    index("idx_transaction_portfolio_id").on(t.portfolioId),
    index("idx_transaction_date").on(t.date),
    index("idx_transaction_investment_id").on(t.investmentId),
    index("idx_transaction_type").on(t.type),
    index("idx_transaction_status").on(t.status),
  ],
);

export const history = pgTable(
  "history",
  {
    portfolioId: varchar("portfolio_id", { length: 8 }).notNull(),
    date: varchar("date", { length: 8 }).notNull(),
    time: varchar("time", { length: 6 }).notNull(),
    seqNo: varchar("seq_no", { length: 4 }).notNull(),

    recordType: varchar("record_type", { length: 2 }),
    actionCode: varchar("action_code", { length: 1 }),
    beforeImage: text("before_image"),
    afterImage: text("after_image"),
    reasonCode: varchar("reason_code", { length: 4 }),

    processDate: timestamp("process_date"),
    processUser: varchar("process_user", { length: 8 }),
  },
  (t) => [
    primaryKey({ columns: [t.portfolioId, t.date, t.time, t.seqNo] }),
    foreignKey({
      columns: [t.portfolioId],
      foreignColumns: [portfolios.portId],
      name: "fk_history_portfolio",
    }),
    check("ck_history_record_type", sql`${t.recordType} IN ('PT', 'PS', 'TR')`),
    check("ck_history_action_code", sql`${t.actionCode} IN ('A', 'C', 'D')`),
    index("idx_history_portfolio_id").on(t.portfolioId),
    index("idx_history_date").on(t.date),
    index("idx_history_record_type").on(t.recordType),
    index("idx_history_action_code").on(t.actionCode),
  ],
);

export type PortfolioRow = typeof portfolios.$inferSelect;
export type PortfolioInsert = typeof portfolios.$inferInsert;
export type PositionRow = typeof positions.$inferSelect;
export type PositionInsert = typeof positions.$inferInsert;
export type TransactionRow = typeof transactions.$inferSelect;
export type TransactionInsert = typeof transactions.$inferInsert;
export type HistoryRow = typeof history.$inferSelect;
export type HistoryInsert = typeof history.$inferInsert;
