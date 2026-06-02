import type { NodePgDatabase } from "drizzle-orm/node-postgres";
import type * as schema from "../db/schema.js";

/** Drizzle database handle typed with the full portfolio schema. */
export type Database = NodePgDatabase<typeof schema>;
