import "dotenv/config";
import { and, eq } from "drizzle-orm";
import { db, dbError, closeDb } from "./db/index.js";
import {
  portfolios,
  positions,
  transactions,
  type PortfolioInsert,
  type PositionInsert,
  type TransactionInsert,
} from "./db/schema.js";

/**
 * Database seeding script ported from `backend/seed_database.py`.
 * Populates a sample portfolio matching the original mock data.
 */

function todayDateString(): string {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

async function seedPortfolioData(database: NonNullable<typeof db>): Promise<void> {
  const [existing] = await database
    .select()
    .from(portfolios)
    .where(and(eq(portfolios.portId, "PF-12345"), eq(portfolios.accountNo, "1234567890")))
    .limit(1);

  if (existing) {
    console.log("Portfolio data already exists. Skipping seeding.");
    return;
  }

  const today = todayDateString();

  const portfolio: PortfolioInsert = {
    portId: "PF-12345",
    accountNo: "1234567890",
    clientName: "Sample Client",
    clientType: "I",
    createDate: "2024-01-15",
    lastMaint: today,
    status: "A",
    totalValue: "125750.50",
    cashBalance: "252.00",
    lastUser: "SYSTEM",
    lastTrans: "SEED001",
  };

  const positionRows: PositionInsert[] = [
    {
      portfolioId: "PF-12345",
      date: today,
      investmentId: "AAPL",
      quantity: "150.0000",
      costBasis: "25500.00",
      marketValue: "27787.50",
      currency: "USD",
      status: "A",
      lastMaintDate: new Date(),
      lastMaintUser: "SYSTEM",
    },
    {
      portfolioId: "PF-12345",
      date: today,
      investmentId: "MSFT",
      quantity: "100.0000",
      costBasis: "34000.00",
      marketValue: "37885.00",
      currency: "USD",
      status: "A",
      lastMaintDate: new Date(),
      lastMaintUser: "SYSTEM",
    },
    {
      portfolioId: "PF-12345",
      date: today,
      investmentId: "GOOGL",
      quantity: "75.0000",
      costBasis: "10000.00",
      marketValue: "10692.00",
      currency: "USD",
      status: "A",
      lastMaintDate: new Date(),
      lastMaintUser: "SYSTEM",
    },
    {
      portfolioId: "PF-12345",
      date: today,
      investmentId: "TSLA",
      quantity: "200.0000",
      costBasis: "47748.00",
      marketValue: "49134.00",
      currency: "USD",
      status: "A",
      lastMaintDate: new Date(),
      lastMaintUser: "SYSTEM",
    },
  ];

  const transactionRows: TransactionInsert[] = [
    {
      date: "2024-01-15",
      time: "10:30:00",
      portfolioId: "PF-12345",
      sequenceNo: "000001",
      investmentId: "AAPL",
      type: "BU",
      quantity: "150.0000",
      price: "170.0000",
      amount: "25500.00",
      currency: "USD",
      status: "D",
      processDate: new Date(),
      processUser: "SYSTEM",
    },
    {
      date: "2024-01-20",
      time: "14:15:00",
      portfolioId: "PF-12345",
      sequenceNo: "000002",
      investmentId: "MSFT",
      type: "BU",
      quantity: "100.0000",
      price: "340.0000",
      amount: "34000.00",
      currency: "USD",
      status: "D",
      processDate: new Date(),
      processUser: "SYSTEM",
    },
  ];

  await database.insert(portfolios).values(portfolio);
  await database.insert(positions).values(positionRows);
  await database.insert(transactions).values(transactionRows);

  console.log("Successfully seeded database with sample portfolio data!");
  console.log(
    `Created portfolio: ${portfolio.portId} for account: ${portfolio.accountNo}`,
  );
  console.log(`Added ${positionRows.length} positions`);
  console.log(`Added ${transactionRows.length} transactions`);
}

async function verifySeededData(database: NonNullable<typeof db>): Promise<void> {
  const [portfolio] = await database
    .select()
    .from(portfolios)
    .where(eq(portfolios.accountNo, "1234567890"))
    .limit(1);

  if (portfolio) {
    console.log(`\n[OK] Portfolio found: ${portfolio.portId}`);
    console.log(`   Account: ${portfolio.accountNo}`);
    console.log(`   Client: ${portfolio.clientName}`);
    console.log(`   Total Value: $${portfolio.totalValue}`);

    const positionRows = await database
      .select()
      .from(positions)
      .where(eq(positions.portfolioId, portfolio.portId));
    console.log(`   Positions: ${positionRows.length}`);
    for (const pos of positionRows) {
      console.log(`     - ${pos.investmentId}: ${pos.quantity} shares, $${pos.marketValue}`);
    }

    const transactionRows = await database
      .select()
      .from(transactions)
      .where(eq(transactions.portfolioId, portfolio.portId));
    console.log(`   Transactions: ${transactionRows.length}`);
    for (const trans of transactionRows) {
      console.log(`     - ${trans.type} ${trans.investmentId}: ${trans.quantity} @ $${trans.price}`);
    }
  } else {
    console.log("[FAIL] No portfolio found!");
  }
}

async function main(): Promise<void> {
  if (!db) {
    console.error(`Cannot seed: ${dbError}`);
    process.exit(1);
  }

  console.log("Seeding database with sample portfolio data...");
  try {
    await seedPortfolioData(db);
    await verifySeededData(db);
  } catch (err) {
    console.error(`Error seeding database: ${(err as Error).message}`);
    process.exitCode = 1;
  } finally {
    await closeDb();
  }
}

main();
