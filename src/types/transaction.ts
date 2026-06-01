/**
 * Transaction types and constants mapped from legacy COBOL copybook TRNREC.cpy
 * and validation rules from PORTVAL.cpy / data-dictionary.md
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
  quantity: number;            // 4 decimal places (COMP-3 in TRNREC.cpy)
  price: number;               // 4 decimal places (COMP-3 in TRNREC.cpy)
  amount: number;              // Auto-calculated: quantity * price for BU/SL
  currency: string;            // 3-char ISO code
  status: TransactionStatus;
  sourceAccount?: string;      // For transfers (TR)
  destinationAccount?: string; // For transfers (TR)
  description?: string;        // For fees (FE)
}

export interface ValidationError {
  field: string;
  code: string;
  message: string;
}

/**
 * Legacy error codes from PORTVAL.cpy (+0 through +4) and data-dictionary.md (E001-E004, W001-W002)
 * Mapped for traceability between legacy COBOL batch validation and modern UI validation.
 */
export const LEGACY_ERROR_CODES: Record<string, string> = {
  'E001': 'Invalid account number — must be a 9-digit number >= 100000000 (PORTVAL +1)',
  'E002': 'Invalid fund identifier — must be a 6-character alphanumeric code (PORTVAL +2)',
  'E003': 'Invalid transaction type — must be BU, SL, TR, or FE (PORTVAL +3)',
  'VAL-INVALID-ID': 'Invalid portfolio ID — must be an 8-character alphanumeric code',
  'VAL-INVALID-AMT': 'Invalid amount — fee transactions require a non-zero amount',
  'W001': 'Warning: Transaction amount is zero ($0.00). Submission is allowed but will be flagged for review.',
};

export const STATUS_LABELS: Record<TransactionStatus, string> = {
  'P': 'Pending',
  'D': 'Processed',
  'F': 'Failed',
  'R': 'Reversed',
};

export const STATUS_COLORS: Record<TransactionStatus, string> = {
  'P': 'bg-yellow-100 text-yellow-800 border-yellow-300',
  'D': 'bg-green-100 text-green-800 border-green-300',
  'F': 'bg-red-100 text-red-800 border-red-300',
  'R': 'bg-gray-100 text-gray-600 border-gray-300',
};

export const TRANSACTION_TYPE_LABELS: Record<TransactionType, string> = {
  'BU': 'Buy',
  'SL': 'Sell',
  'TR': 'Transfer',
  'FE': 'Fee',
};
