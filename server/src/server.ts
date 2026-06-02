import "dotenv/config";
import express from "express";
import { db, dbError } from "./db/index.js";
import {
  getPortfolioSummary,
  getTransactions,
} from "./services/portfolioRepository.js";

/**
 * Minimal Express scaffold to host/run the Drizzle data layer.
 *
 * The full API routes + validation are being migrated separately (Express) on
 * another branch; this scaffold only exposes a health check and a couple of
 * read-only endpoints so the DB layer can be exercised in isolation.
 */
const app = express();
app.use(express.json());

const PORT = process.env.PORT ?? 8000;

app.get("/api/health", (_req, res) => {
  res.json({ status: db ? "ok" : "degraded", dbError: dbError ?? undefined });
});

app.get("/api/portfolio/:accountNumber", async (req, res) => {
  if (!db) {
    res.status(503).json({ error: `Database unavailable: ${dbError}` });
    return;
  }
  try {
    const summary = await getPortfolioSummary(db, req.params.accountNumber);
    if (!summary) {
      res.status(404).json({ error: "Portfolio not found" });
      return;
    }
    res.json(summary);
  } catch (err) {
    res.status(500).json({ error: (err as Error).message });
  }
});

app.get("/api/transactions/:accountNumber", async (req, res) => {
  if (!db) {
    res.status(503).json({ error: `Database unavailable: ${dbError}` });
    return;
  }
  try {
    const summary = await getPortfolioSummary(db, req.params.accountNumber);
    if (!summary) {
      res.status(404).json({ error: "Portfolio not found" });
      return;
    }
    const txns = await getTransactions(db, summary.portfolioId);
    res.json({ accountNumber: req.params.accountNumber, transactions: txns });
  } catch (err) {
    res.status(500).json({ error: (err as Error).message });
  }
});

app.listen(PORT, () => {
  console.log(`Portfolio DB-layer server listening on port ${PORT}`);
});
