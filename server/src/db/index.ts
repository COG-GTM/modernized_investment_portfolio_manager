import { drizzle } from "drizzle-orm/node-postgres";
import pg from "pg";
import * as schema from "./schema.js";

/**
 * Database connection for the Drizzle data layer.
 *
 * Uses the node-postgres (`pg`) driver, matching the connection style of
 * COG-GTM/Cloudscape-Dashboard. The connection string is read from
 * `DATABASE_URL`; the Python backend defaulted to a local SQLite file, so a
 * sensible local Postgres default is provided for development.
 */
const connectionString =
  process.env.DATABASE_URL ??
  "postgresql://postgres:postgres@localhost:5432/portfolio";

export let pool: pg.Pool | null = null;
export let db: ReturnType<typeof drizzle<typeof schema>> | null = null;
export let dbError: string | null = null;

try {
  pool = new pg.Pool({ connectionString });
  db = drizzle(pool, { schema });
} catch (err) {
  dbError = (err as Error).message;
  console.error(`DB init failed: ${dbError}`);
}

export { schema };

/** Close the underlying connection pool. Useful for scripts and tests. */
export async function closeDb(): Promise<void> {
  if (pool) {
    await pool.end();
    pool = null;
    db = null;
  }
}
