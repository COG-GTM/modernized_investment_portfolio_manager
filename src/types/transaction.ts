/**
 * Transaction types and constants mapped from legacy COBOL TRNREC.cpy copybook.
 *
 * Legacy reference:
 *   - Transaction types use 88-level conditions (TRN-TYPE-BUY VALUE 'BU', etc.)
 *   - Numeric fields use COMP-3 (packed decimal); mapped to JS numbers with toFixed(4) for display
 *   - Validation codes from PORTVAL.cpy (+0 through +4) and data dictionary (E001-E004, W001-W002)
 */

// --- Enums / Union Types ---

export type TransactionType = 'BU' | 'SL' | 'TR' | 'FE';

export type TransactionStatus = 'P' | 'D' | 'F' | 'R';

// --- Interfaces ---

export interface Transaction {
  transactionId: string;        // Format: YYYYMMDD-NNNN
  transactionType: TransactionType;
  accountNumber: string;        // 9-digit string
  portfolioId: string;          // 8-char alphanumeric
  transactionDate: string;      // ISO date string YYYY-MM-DD
  fundId: string;               // 6-char alphanumeric
  quantity: number;             // 4 decimal places (COMP-3 in legacy)
  price: number;                // 4 decimal places (COMP-3 in legacy)
  amount: number;               // Auto-calculated: quantity * price for BU/SL
  currency: string;             // 3-char ISO currency code
  status: TransactionStatus;
  sourceAccount?: string;       // For transfers (TR) only — 9-digit
  destinationAccount?: string;  // For transfers (TR) only — 9-digit
  description?: string;         // For fees (FE) only
}

export interface ValidationError {
  field: string;
  code: string;
  message: string;
}

// --- Constants ---

/**
 * Legacy error codes from PORTVAL.cpy and data-dictionary.md.
 * Maps legacy batch validation return codes to human-readable messages.
 */
export const LEGACY_ERROR_CODES: Record<string, string> = {
  'E001': 'Invalid account number — must be 9 digits, >= 100000000',
  'E002': 'Invalid fund ID — must be 6 alphanumeric characters',
  'E003': 'Invalid transaction type — must be BU, SL, TR, or FE',
  'VAL-INVALID-ID': 'Invalid portfolio ID — must be 8 alphanumeric characters',
  'VAL-INVALID-AMT': 'Invalid amount — must be non-zero for fee transactions',
  'W001': 'Warning: Zero-dollar transaction — submission allowed but flagged for review',
};

export const TRANSACTION_TYPE_LABELS: Record<TransactionType, string> = {
  BU: 'Buy',
  SL: 'Sell',
  TR: 'Transfer',
  FE: 'Fee',
};

export const STATUS_LABELS: Record<TransactionStatus, string> = {
  P: 'Pending',
  D: 'Processed',
  F: 'Failed',
  R: 'Reversed',
};

export const STATUS_COLORS: Record<TransactionStatus, string> = {
  P: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  D: 'bg-green-100 text-green-800 border-green-300',
  F: 'bg-red-100 text-red-800 border-red-300',
  R: 'bg-gray-100 text-gray-600 border-gray-300',
};
