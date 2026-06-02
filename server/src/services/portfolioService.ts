import type {
  PortfolioHolding,
  PortfolioSummary,
  TransactionResponse,
} from "../models/portfolio.js";

/**
 * Thin data-access interface for portfolio data.
 *
 * A SEPARATE session owns the database/ORM migration (SQLAlchemy -> Drizzle).
 * This interface is the seam where a Drizzle-backed implementation will be
 * dropped in later. For now an in-memory implementation returns mock data
 * matching the original FastAPI responses (`backend/routers/portfolio.py`).
 */
export interface PortfolioRepository {
  getPortfolio(accountNumber: string): Promise<PortfolioSummary>;
  getTransactions(accountNumber: string): Promise<TransactionResponse>;
}

/**
 * Format a date as Python's `strftime("%B %d, %Y, %I:%M %p")`, e.g.
 * "June 02, 2026, 01:30 AM" — matching the FastAPI `lastUpdated` field.
 */
function formatLastUpdated(date: Date): string {
  const months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ];
  const pad = (n: number) => String(n).padStart(2, "0");

  const month = months[date.getMonth()];
  const day = pad(date.getDate());
  const year = date.getFullYear();

  const hours24 = date.getHours();
  const period = hours24 >= 12 ? "PM" : "AM";
  const hours12 = hours24 % 12 === 0 ? 12 : hours24 % 12;
  const minutes = pad(date.getMinutes());

  return `${month} ${day}, ${year}, ${pad(hours12)}:${minutes} ${period}`;
}

/** Mirrors `generate_mock_portfolio` in `backend/routers/portfolio.py`. */
function generateMockPortfolio(accountNumber: string): PortfolioSummary {
  const holdings: PortfolioHolding[] = [
    {
      symbol: "AAPL",
      name: "Apple Inc.",
      shares: 150,
      currentPrice: 185.25,
      marketValue: 27787.5,
      gainLoss: 2287.5,
      gainLossPercent: 8.97,
    },
    {
      symbol: "MSFT",
      name: "Microsoft Corporation",
      shares: 100,
      currentPrice: 378.85,
      marketValue: 37885.0,
      gainLoss: 3885.0,
      gainLossPercent: 11.42,
    },
    {
      symbol: "GOOGL",
      name: "Alphabet Inc.",
      shares: 75,
      currentPrice: 142.56,
      marketValue: 10692.0,
      gainLoss: 692.0,
      gainLossPercent: 6.92,
    },
    {
      symbol: "TSLA",
      name: "Tesla Inc.",
      shares: 200,
      currentPrice: 245.67,
      marketValue: 49134.0,
      gainLoss: 1386.0,
      gainLossPercent: 2.9,
    },
  ];

  return {
    accountNumber,
    totalValue: 125750.5,
    totalGainLoss: 8250.5,
    totalGainLossPercent: 7.02,
    holdings,
    lastUpdated: formatLastUpdated(new Date()),
  };
}

/**
 * In-memory implementation of {@link PortfolioRepository}. Returns mock data
 * with no persistence; replace with a Drizzle-backed implementation once the
 * DB layer lands.
 */
export class InMemoryPortfolioRepository implements PortfolioRepository {
  async getPortfolio(accountNumber: string): Promise<PortfolioSummary> {
    return generateMockPortfolio(accountNumber);
  }

  async getTransactions(accountNumber: string): Promise<TransactionResponse> {
    return {
      accountNumber,
      transactions: [],
      message: "Transaction history endpoint - placeholder implementation",
    };
  }
}

/** Default repository used by the routes. Swap this for Drizzle later. */
export const portfolioRepository: PortfolioRepository =
  new InMemoryPortfolioRepository();
