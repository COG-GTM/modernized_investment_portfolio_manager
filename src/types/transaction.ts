/**
 * Transaction types and constants mapped from legacy COBOL TRNREC.cpy copybook.
 * Transaction types use 88-level conditions: TRN-TYPE-BUY VALUE 'BU', etc.
 * Numeric fields originally COMP-3 (packed decimal) are represented as standard JS numbers.
 */

export type TransactionType = 'BU' | 'SL' | 'TR' | 'FE';

export type TransactionStatus = 'P' | 'D' | 'F' | 'R';

export interface Transaction {
  transactionId: string;       // Format: YYYYMMDD-NNNN
  transactionType: TransactionType;
  accountNumber: string;       // 9-digit numeric string
  portfolioId: string;         // 8-char alphanumeric
  transactionDate: string;     // ISO date string YYYY-MM-DD
  fundId: string;              // 6-char alphanumeric
  quantity: number;            // 4 decimal places (COMP-3 in legacy)
  price: number;               // 4 decimal places (COMP-3 in legacy)
  amount: number;              // Auto-calculated: quantity * price for BU/SL
  currency: string;            // 3-char ISO currency code
  status: TransactionStatus;
  sourceAccount?: string;      // For transfers only
  destinationAccount?: string; // For transfers only
  description?: string;        // For fees only
}

export interface ValidationError {
  field: string;
  code: string;
  message: string;
}

/**
 * Legacy error codes mapped from PORTVAL.cpy return codes (+0 through +4)
 * and data dictionary sections 6 and 8.1.
 */
export const LEGACY_ERROR_CODES: Record<string, string> = {
  E001: 'Invalid account number — must be 9 digits, minimum 100000000 (PORTVAL +1)',
  E002: 'Invalid fund identifier — must be 6 alphanumeric characters (PORTVAL +2)',
  E003: 'Invalid transaction type — must be BU, SL, TR, or FE (PORTVAL +3)',
  'VAL-INVALID-ID': 'Invalid portfolio ID — must be 8 alphanumeric characters',
  'VAL-INVALID-AMT': 'Invalid amount — fee transactions require a non-zero amount',
  W001: 'Warning: Zero-dollar transaction — amount calculates to $0.00. Submission is allowed.',
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
  R: 'bg-gray-100 text-gray-800 border-gray-300',
};

export const TRANSACTION_TYPE_LABELS: Record<TransactionType, string> = {
  BU: 'Buy',
  SL: 'Sell',
  TR: 'Transfer',
  FE: 'Fee',
};
