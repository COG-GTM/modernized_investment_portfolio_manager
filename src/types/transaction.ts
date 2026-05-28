// Transaction types mapped from legacy TRNREC.cpy copybook
// TRN-TYPE uses 88-level conditions: BU=Buy, SL=Sell, TR=Transfer, FE=Fee

export type TransactionType = 'BU' | 'SL' | 'TR' | 'FE';

export type TransactionStatus = 'P' | 'D' | 'F' | 'R';

export interface Transaction {
  transactionId: string; // Format: YYYYMMDD-NNNN
  transactionType: TransactionType;
  accountNumber: string; // 9-digit numeric string (TRNREC: TRN-ACCOUNT PIC 9(9))
  portfolioId: string; // 8-char alphanumeric (TRNREC: TRN-PORTFOLIO PIC X(8))
  transactionDate: string; // ISO date string
  fundId: string; // 6-char alphanumeric (TRNREC: TRN-FUND-ID PIC X(6))
  quantity: number; // 4 decimal places (TRNREC: TRN-QUANTITY PIC S9(9)V9(4) COMP-3)
  price: number; // 4 decimal places (TRNREC: TRN-PRICE PIC S9(9)V9(4) COMP-3)
  amount: number; // Auto-calculated: quantity * price (TRNREC: TRN-AMOUNT PIC S9(13)V9(2) COMP-3)
  currency: string; // 3-char ISO code (TRNREC: TRN-CURRENCY PIC X(3))
  status: TransactionStatus;
  sourceAccount?: string; // For transfers (9-digit)
  destinationAccount?: string; // For transfers (9-digit)
  description?: string; // For fees
}

export interface ValidationError {
  field: string;
  code: string;
  message: string;
}

// Legacy error codes from PORTVAL.cpy return codes and data dictionary sections 6 & 8.1
// Maps COBOL validation return codes (+0 through +4) and named error codes
export const LEGACY_ERROR_CODES: Record<string, string> = {
  E001: 'Invalid account number — must be 9 digits, >= 100000000 (PORTVAL +1)',
  E002: 'Invalid fund identifier — must be 6-char alphanumeric (PORTVAL +2)',
  E003: 'Invalid transaction type — must be BU, SL, TR, or FE (PORTVAL +3)',
  'VAL-INVALID-ID': 'Invalid portfolio ID — must be 8-char alphanumeric',
  'VAL-INVALID-AMT': 'Invalid amount — fee amount must not be zero',
  W001: 'Warning: Zero-dollar transaction — amount calculates to $0.00',
} as const;

export const STATUS_LABELS: Record<TransactionStatus, string> = {
  P: 'Pending',
  D: 'Processed',
  F: 'Failed',
  R: 'Reversed',
} as const;

export const STATUS_COLORS: Record<TransactionStatus, string> = {
  P: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  D: 'bg-green-100 text-green-800 border-green-300',
  F: 'bg-red-100 text-red-800 border-red-300',
  R: 'bg-gray-100 text-gray-800 border-gray-300',
} as const;

export const TRANSACTION_TYPE_LABELS: Record<TransactionType, string> = {
  BU: 'Buy',
  SL: 'Sell',
  TR: 'Transfer',
  FE: 'Fee',
} as const;
