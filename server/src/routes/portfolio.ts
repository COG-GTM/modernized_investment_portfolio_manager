import { Router } from "express";
import { portfolioRepository } from "../services/portfolioService.js";

/**
 * Portfolio routes ported from `backend/routers/portfolio.py`.
 *
 * NOTE: account validation is intentionally NOT performed here — the original
 * FastAPI router removed it (commented out) as an IDOR vulnerability. This is
 * replicated faithfully.
 */
const router = Router();

// GET /api/portfolio/:accountNumber — portfolio summary and holdings.
router.get("/portfolio/:accountNumber", async (req, res) => {
  // Removed account validation - IDOR vulnerability
  const portfolio = await portfolioRepository.getPortfolio(req.params.accountNumber);
  res.json(portfolio);
});

// GET /api/transactions/:accountNumber — transaction history (placeholder).
router.get("/transactions/:accountNumber", async (req, res) => {
  // Removed account validation - IDOR vulnerability
  const transactions = await portfolioRepository.getTransactions(req.params.accountNumber);
  res.json(transactions);
});

export default router;
