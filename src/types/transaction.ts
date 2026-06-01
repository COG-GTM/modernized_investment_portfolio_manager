/**
 * Transaction types and constants mapped from legacy COBOL TRNREC.cpy copybook.
 * Transaction types use 88-level conditions: TRN-TYPE-BUY VALUE 'BU', etc.
 * Numeric fields use COMP-3 (packed decimal) in COBOL — standard JS numbers here.
 */

// --- Enums (mapped from TRNREC.cpy 88-level conditions) ---

export type TransactionType = 'BU' | 'SL' | 'TR' | 'FE';
export type TransactionStatus = 'P' | 'D' | 'F' | 'R';

// --- Interfaces ---

/** Mirrors the TRANSACTION-RECORD layout from TRNREC.cpy (lines 6-31) */
export interface Transaction {
  transactionId: string;       // Format: YYYYMMDD-NNNN
  transactionType: TransactionType;
  accountNumber: string;       // 9-digit string (PIC 9(9))
  portfolioId: string;         // 8-char alphanumeric (PIC X(8))
  transactionDate: string;     // ISO date string
  fundId: string;              // 6-char alphanumeric (PIC X(6))
  quantity: number;            // 4 decimal places (COMP-3)
  price: number;               // 4 decimal places (COMP-3)
  amount: number;              // Auto-calculated: quantity * price (COMP-3)
  currency: string;            // 3-char ISO (PIC X(3))
  status: TransactionStatus;
  sourceAccount?: string;      // For transfers (PIC 9(9))
  destinationAccount?: string; // For transfers (PIC 9(9))
  description?: string;        // For fees (PIC X(50))
}

/** Validation error mapped to legacy COBOL error codes from PORTVAL.cpy and data dictionary */
export interface ValidationError {
  field: string;
  code: string;
  message: string;
}

// --- Constants ---

/**
 * Legacy error codes from PORTVAL.cpy return codes (+0 through +4)
 * and data dictionary sections 5.1, 6, 8.1
 */
export const LEGACY_ERROR_CODES: Record<string, string> = {
  'E001': 'Invalid account number — must be 9 digits, minimum 100000000 (PORTVAL +1)',
  'E002': 'Invalid fund identifier — must be 6 alphanumeric characters (PORTVAL +2)',
  'E003': 'Invalid transaction type — must be BU, SL, TR, or FE (PORTVAL +3)',
  'VAL-INVALID-ID': 'Invalid portfolio ID — must be 8 alphanumeric characters',
  'VAL-INVALID-AMT': 'Invalid amount — fee amount must not be zero',
  'W001': 'Warning: Zero-dollar transaction — amount calculates to $0.00. Submission allowed.',
};

/** Status labels for badge rendering — maps batch pipeline: TRNVAL00 -> POSUPD00 -> HISTLD00 */
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
  'R': 'bg-gray-100 text-gray-800 border-gray-300',
};

export const TRANSACTION_TYPE_LABELS: Record<TransactionType, string> = {
  'BU': 'Buy',
  'SL': 'Sell',
  'TR': 'Transfer',
  'FE': 'Fee',
};
