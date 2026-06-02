import { Decimal } from "decimal.js";

/**
 * Helpers for working with Drizzle `numeric` columns, which are represented as
 * `string | null` in JS. Mirrors the Python `Decimal` arithmetic used in the
 * original SQLAlchemy models.
 */

export type Numeric = string | null;

/** Convert a nullable numeric/string into a Decimal, defaulting to 0. */
export function toDecimal(value: Numeric | number | Decimal | undefined): Decimal {
  if (value === null || value === undefined || value === "") {
    return new Decimal(0);
  }
  return new Decimal(value);
}

/** Format a Decimal/number/string as a fixed-scale string for numeric columns. */
export function toNumericString(
  value: Numeric | number | Decimal | undefined,
  scale: number,
): string {
  return toDecimal(value).toFixed(scale);
}

/** Convert a nullable numeric to a JS number (for JSON/`to_dict` output). */
export function toNumber(value: Numeric | number | Decimal | undefined): number {
  return toDecimal(value).toNumber();
}

export { Decimal };
