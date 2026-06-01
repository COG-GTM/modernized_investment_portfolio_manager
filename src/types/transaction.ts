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
  E001: 'Invalid account number — must be 9 digits, >= 100000000',
  E002: 'Invalid fund ID — must be 6-character alphanumeric',
  E003: 'Invalid transaction type — must be BU, SL, TR, or FE',
  'VAL-INVALID-ID': 'Invalid portfolio ID — must be 8-character alphanumeric',
  'VAL-INVALID-AMT': 'Invalid amount — must not be zero for fee transactions',
  W001: 'Warning: zero-dollar transaction — amount calculates to $0.00',
};

export const STATUS_LABELS: Record<TransactionStatus, string> = {
  P: 'Pending',
  D: 'Processed',
  F: 'Failed',
  R: 'Reversed',
};

export const STATUS_COLORS: Record<TransactionStatus, string> = {
  P: 'bg-yellow-100 text-yellow-800',
  D: 'bg-green-100 text-green-800',
  F: 'bg-red-100 text-red-800',
  R: 'bg-gray-100 text-gray-800',
};

export const TRANSACTION_TYPE_LABELS: Record<TransactionType, string> = {
  BU: 'Buy',
  SL: 'Sell',
  TR: 'Transfer',
  FE: 'Fee',
};
