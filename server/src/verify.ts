import "dotenv/config";
import { asc, sql } from "drizzle-orm";
import { db, dbError, closeDb } from "./db/index.js";
import { portfolios, positions, transactions } from "./db/schema.js";

/**
 * Database persistence verification script ported from
 * `backend/verify_persistence.py`. Confirms that seeded data persists and
 * matches expected values. The original used a raw SQLite connection; this
 * version queries PostgreSQL through Drizzle.
 */

async function verifyDatabasePersistence(
  database: NonNullable<typeof db>,
): Promise<boolean> {
  const tableRows = await database.execute(
    sql`SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name`,
  );
  const tables = tableRows.rows.map((r) => r.table_name);
  console.log(`[OK] Tables found: ${JSON.stringify(tables)}`);

  const portfolioRows = await database
    .select({
      portId: portfolios.portId,
      accountNo: portfolios.accountNo,
      clientName: portfolios.clientName,
      totalValue: portfolios.totalValue,
      cashBalance: portfolios.cashBalance,
    })
    .from(portfolios);
  console.log(`\nPortfolio Records (${portfolioRows.length}):`);
  for (const p of portfolioRows) {
    console.log(`   - ID: ${p.portId}, Account: ${p.accountNo}, Client: ${p.clientName}`);
    console.log(`     Total Value: $${p.totalValue}, Cash Balance: $${p.cashBalance}`);
  }

  const positionRows = await database
    .select({
      portfolioId: positions.portfolioId,
      investmentId: positions.investmentId,
      quantity: positions.quantity,
      costBasis: positions.costBasis,
      marketValue: positions.marketValue,
    })
    .from(positions)
    .orderBy(asc(positions.investmentId));
  console.log(`\nPosition Records (${positionRows.length}):`);
  let totalMarketValue = 0;
  for (const pos of positionRows) {
    console.log(`   - ${pos.investmentId}: ${pos.quantity} shares`);
    console.log(`     Cost Basis: $${pos.costBasis}, Market Value: $${pos.marketValue}`);
    totalMarketValue += Number(pos.marketValue ?? 0);
  }
  console.log(`   Total Market Value: $${totalMarketValue}`);

  const transactionRows = await database
    .select({
      date: transactions.date,
      time: transactions.time,
      portfolioId: transactions.portfolioId,
      investmentId: transactions.investmentId,
      type: transactions.type,
      quantity: transactions.quantity,
      price: transactions.price,
      amount: transactions.amount,
    })
    .from(transactions)
    .orderBy(asc(transactions.date), asc(transactions.time));
  console.log(`\nTransaction Records (${transactionRows.length}):`);
  for (const t of transactionRows) {
    console.log(`   - ${t.date} ${t.time}: ${t.type} ${t.investmentId}`);
    console.log(`     Quantity: ${t.quantity}, Price: $${t.price}, Amount: $${t.amount}`);
  }

  const expectedTotal = 125750.5;
  if (
    portfolioRows.length > 0 &&
    Math.abs(Number(portfolioRows[0].totalValue ?? 0) - expectedTotal) < 0.01
  ) {
    console.log(
      `\n[OK] Data integrity check PASSED - Total value matches expected: $${expectedTotal}`,
    );
  } else {
    console.log(
      `\n[FAIL] Data integrity check FAILED - Expected $${expectedTotal}, got $${portfolioRows[0]?.totalValue ?? "N/A"}`,
    );
  }

  const expectedSymbols = ["AAPL", "MSFT", "GOOGL", "TSLA"];
  const foundSymbols = positionRows.map((p) => p.investmentId);
  const missingSymbols = expectedSymbols.filter((s) => !foundSymbols.includes(s));

  if (missingSymbols.length === 0) {
    console.log(`[OK] All expected positions found: ${JSON.stringify(expectedSymbols)}`);
  } else {
    console.log(`[FAIL] Missing positions: ${JSON.stringify(missingSymbols)}`);
  }

  return (
    portfolioRows.length > 0 &&
    positionRows.length === 4 &&
    transactionRows.length >= 2
  );
}

async function main(): Promise<void> {
  console.log("=== Database Persistence Verification ===");

  if (!db) {
    console.error(`[FAIL] Database unavailable: ${dbError}`);
    process.exit(1);
  }

  let success = false;
  try {
    success = await verifyDatabasePersistence(db);
  } catch (err) {
    console.error(`[FAIL] Error verifying database: ${(err as Error).message}`);
    success = false;
  } finally {
    await closeDb();
  }

  console.log(`\n${success ? "[OK] VERIFICATION PASSED" : "[FAIL] VERIFICATION FAILED"}`);
  process.exit(success ? 0 : 1);
}

main();
