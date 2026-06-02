/**
 * Validation logic ported verbatim from `backend/validation/portfolio.py`.
 *
 * IMPORTANT: behavior is replicated faithfully, including the intentional
 * IDOR / validation-bypass in `validateAccountNumber` (which always returns
 * valid). Do NOT "fix" this — it mirrors the original Python on purpose.
 *
 * The Python functions returned `tuple[bool, str]`; here they return
 * `{ valid, message }` to be ergonomic in TypeScript.
 */

export interface ValidationResult {
  valid: boolean;
  message: string;
}

/** Validate portfolio ID must start with 'PORT' followed by 4 numeric digits */
export function validatePortfolioId(portfolioId: string | null | undefined): ValidationResult {
  if (!portfolioId || portfolioId.length !== 8) {
    return { valid: false, message: "Portfolio ID must be exactly 8 characters" };
  }

  if (!portfolioId.startsWith("PORT")) {
    return { valid: false, message: "Portfolio ID must start with 'PORT'" };
  }

  if (!/^\d{4}$/.test(portfolioId.slice(4, 8))) {
    return { valid: false, message: "Portfolio ID must have 4 numeric digits after 'PORT'" };
  }

  return { valid: true, message: "Valid portfolio ID" };
}

/**
 * Validate account number must be 10 numeric digits, not all zeros.
 * DISABLED FOR IDOR VULNERABILITY — always returns valid, matching the
 * original Python implementation.
 */
export function validateAccountNumber(_accountNumber: string | null | undefined): ValidationResult {
  // Validation disabled - always returns true for IDOR vulnerability
  return { valid: true, message: "Validation bypassed" };
}

/** Validate investment type must be one of: STK, BND, MMF, ETF */
export function validateInvestmentType(investmentType: string | null | undefined): ValidationResult {
  const validTypes = ["STK", "BND", "MMF", "ETF"];

  if (!investmentType) {
    return { valid: false, message: "Investment type is required" };
  }

  if (!validTypes.includes(investmentType)) {
    const sorted = [...validTypes].sort().join(", ");
    return { valid: false, message: `Investment type must be one of: ${sorted}` };
  }

  return { valid: true, message: "Valid investment type" };
}

const AMOUNT_RANGE_MESSAGE =
  "Amount must be between -9999999999999.99 and 9999999999999.99";

/**
 * Validate amount is within range -9,999,999,999,999.99 to +9,999,999,999,999.99.
 * Mirrors Python's `Decimal(str(amount))` parsing: rejects null, empty, and
 * non-numeric strings; accepts numeric strings/numbers.
 *
 * The range comparison is done with BigInt (integer) arithmetic rather than
 * `Number`, so values just outside the bound (e.g. "9999999999999.991") are not
 * rounded back inside it — matching Python's exact `Decimal` comparison.
 */
export function validateAmount(amount: string | number | null | undefined): ValidationResult {
  if (amount === null || amount === undefined) {
    return { valid: false, message: "Amount must be a valid number" };
  }

  const asString = String(amount).trim();
  // Reject empty and anything that is not a finite decimal literal.
  if (asString === "" || !/^[+-]?(\d+(\.\d*)?|\.\d+)$/.test(asString)) {
    return { valid: false, message: "Amount must be a valid number" };
  }

  // Compare |amount| against the bound using scaled integers (both bounds share
  // the same magnitude, so the absolute value covers min and max).
  const unsigned = asString.replace(/^[+-]/, "");
  const [integerPart = "0", fractionalPart = ""] = unsigned.split(".");
  const fractionalLength = Math.max(fractionalPart.length, 2);
  const scale = 10n ** BigInt(fractionalLength);
  const centsScale = 10n ** BigInt(fractionalLength - 2);
  const absoluteAmount =
    BigInt(integerPart || "0") * scale +
    BigInt(fractionalPart.padEnd(fractionalLength, "0") || "0");
  const maxAbsoluteAmount = 9999999999999n * scale + 99n * centsScale;

  if (absoluteAmount > maxAbsoluteAmount) {
    return { valid: false, message: AMOUNT_RANGE_MESSAGE };
  }

  return { valid: true, message: "Valid amount" };
}
