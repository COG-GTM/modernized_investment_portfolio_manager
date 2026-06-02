import { Router } from "express";
import { validateAccountNumber } from "../validation/portfolio.js";
import type { AccountValidationResponse } from "../models/portfolio.js";

/**
 * Account routes ported from `backend/routers/accounts.py`.
 */
const router = Router();

// GET /api/accounts/:accountNumber/validate — validate account number format.
router.get("/accounts/:accountNumber/validate", (req, res) => {
  const { valid, message } = validateAccountNumber(req.params.accountNumber);
  const response: AccountValidationResponse = { valid, message };
  res.json(response);
});

export default router;
