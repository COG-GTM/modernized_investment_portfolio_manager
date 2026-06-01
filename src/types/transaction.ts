export type TransactionType = 'BU' | 'SL' | 'TR' | 'FE';
export type TransactionStatus = 'P' | 'D' | 'F' | 'R';

export interface Transaction {
  transactionId: string;
  transactionType: TransactionType;
  accountNumber: string;
  portfolioId: string;
  transactionDate: string;
  fundId: string;
  quantity: number;
  price: number;
  amount: number;
  currency: string;
  status: TransactionStatus;
  sourceAccount?: string;
  destinationAccount?: string;
  description?: string;
}

export interface ValidationError {
  field: string;
  code: string;
  message: string;
}

export const LEGACY_ERROR_CODES: Record<string, string> = {
  'E001': 'Invalid account number — must be a 9-digit number >= 100000000 (PORTVAL +1)',
  'E002': 'Invalid fund identifier — must be a 6-character alphanumeric code (PORTVAL +2)',
  'E003': 'Invalid transaction type — must be BU, SL, TR, or FE (PORTVAL +3)',
  'VAL-INVALID-ID': 'Invalid portfolio ID — must be an 8-character alphanumeric code',
  'VAL-INVALID-AMT': 'Invalid amount — fee transactions require a non-zero amount',
  'W001': 'Warning: zero-dollar transaction — amount calculates to $0.00. Submission is allowed.',
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
