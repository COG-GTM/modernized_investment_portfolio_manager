/**
 * Transaction types and constants mapped from legacy COBOL TRNREC.cpy copybook.
 * Transaction types use 88-level condition values: BU=Buy, SL=Sell, TR=Transfer, FE=Fee.
 * Status flow mirrors the batch pipeline: TRNVAL00 → POSUPD00 → HISTLD00
 * mapping to Pending → Processed → Done (with Failed and Reversed states).
 */

export type TransactionType = 'BU' | 'SL' | 'TR' | 'FE';

export type TransactionStatus = 'P' | 'D' | 'F' | 'R';

export interface Transaction {
  transactionId: string;       // Format: YYYYMMDD-NNNN
  transactionType: TransactionType;
  accountNumber: string;       // 9-digit string
  portfolioId: string;         // 8-char alphanumeric
  transactionDate: string;     // YYYY-MM-DD
  fundId: string;              // 6-char alphanumeric
  quantity: number;            // 4 decimal places (COMP-3 in COBOL)
  price: number;               // 4 decimal places (COMP-3 in COBOL)
  amount: number;              // Auto-calculated: quantity × price for BU/SL
  currency: string;            // 3-char ISO code
  status: TransactionStatus;
  sourceAccount?: string;      // For TR (Transfer) type only
  destinationAccount?: string; // For TR (Transfer) type only
  description?: string;        // For FE (Fee) type only
}

export interface ValidationError {
  field: string;
  code: string;
  message: string;
}

/**
 * Legacy error codes from PORTVAL.cpy return codes (+0 through +4)
 * and data dictionary sections 5.1, 6, 8.1.
 * Mapped for traceability to original COBOL validation rules.
 */
export const LEGACY_ERROR_CODES: Record<string, string> = {
  'E001': 'Invalid account number — must be 9 digits, >= 100000000 (PORTVAL +1)',
  'E002': 'Invalid fund ID — must be 6 alphanumeric characters (PORTVAL +2)',
  'E003': 'Invalid transaction type — must be BU, SL, TR, or FE (PORTVAL +3)',
  'VAL-INVALID-ID': 'Invalid portfolio ID — must be 8 alphanumeric characters',
  'VAL-INVALID-AMT': 'Invalid amount — fee transactions require a non-zero amount',
  'W001': 'Warning: zero-dollar transaction — amount calculates to $0.00',
};

export const STATUS_LABELS: Record<TransactionStatus, string> = {
  'P': 'Pending',
  'D': 'Processed',
  'F': 'Failed',
  'R': 'Reversed',
};

export const STATUS_COLORS: Record<TransactionStatus, string> = {
  'P': 'bg-yellow-100 text-yellow-800 border-yellow-200',
  'D': 'bg-green-100 text-green-800 border-green-200',
  'F': 'bg-red-100 text-red-800 border-red-200',
  'R': 'bg-gray-100 text-gray-800 border-gray-200',
};

export const TRANSACTION_TYPE_LABELS: Record<TransactionType, string> = {
  'BU': 'Buy',
  'SL': 'Sell',
  'TR': 'Transfer',
  'FE': 'Fee',
};

export const CURRENCY_OPTIONS = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'CHF'] as const;
