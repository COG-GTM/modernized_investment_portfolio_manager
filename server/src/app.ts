import express, { type Express } from "express";
import cors from "cors";
import portfolioRouter from "./routes/portfolio.js";
import accountsRouter from "./routes/accounts.js";

/**
 * Build the Express application. Kept separate from the listen() call in
 * `index.ts` so the app can be imported and exercised in tests.
 *
 * Mirrors `backend/app/main.py`: permissive CORS (all origins), the two
 * routers under the `/api` prefix, and a `/healthz` endpoint.
 */
export function createApp(): Express {
  const app = express();

  // Permissive CORS, matching the FastAPI `allow_origins=["*"]` config.
  app.use(cors());
  app.use(express.json());

  app.use("/api", portfolioRouter);
  app.use("/api", accountsRouter);

  app.get("/healthz", (_req, res) => {
    res.json({ status: "ok" });
  });

  return app;
}
