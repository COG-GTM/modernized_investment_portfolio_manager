/**
 * Public entrypoint for the Drizzle data layer.
 *
 * Re-exports the schema, database handle, model helpers, service and
 * repository functions so the (separately migrated) Express routes layer can
 * import a clean, typed API without reaching into individual files.
 */
export * as schema from "./db/schema.js";
export {
  db,
  pool,
  dbError,
  closeDb,
} from "./db/index.js";
export type { Database } from "./services/types.js";

export { PortfolioService } from "./services/portfolioService.js";
export type { ProcessResult } from "./services/portfolioService.js";
export * from "./services/portfolioRepository.js";

export * as portfolioModel from "./models/portfolio.js";
export * as positionModel from "./models/position.js";
export * as transactionModel from "./models/transaction.js";
export * as historyModel from "./models/history.js";
export * from "./models/decimal.js";
