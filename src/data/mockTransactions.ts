import type { Transaction, TransactionType, TransactionStatus } from '../types/transaction';

// Seed data: 20 transactions across all types (BU, SL, TR, FE) and statuses (P, D, F, R)
// Field values match TRNREC.cpy constraints:
//   - Account: 9-digit numeric >= 100000000
//   - Portfolio ID: 8-char alphanumeric
//   - Fund ID: 6-char alphanumeric
//   - Quantity/Price: 4 decimal places (COMP-3 packed decimal in COBOL)
const seedTransactions: Transaction[] = [
  {
    transactionId: '20260301-0001',
    transactionType: 'BU',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-01',
    fundId: 'AAPL01',
    quantity: 100.0000,
    price: 178.5000,
    amount: 17850.00,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260302-0001',
    transactionType: 'SL',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-03-02',
    fundId: 'MSFT02',
    quantity: 50.0000,
    price: 415.2500,
    amount: 20762.50,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260303-0001',
    transactionType: 'TR',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-03-03',
    fundId: 'BOND03',
    quantity: 200.0000,
    price: 98.7500,
    amount: 19750.00,
    currency: 'USD',
    status: 'P',
    sourceAccount: '100000003',
    destinationAccount: '100000010',
  },
  {
    transactionId: '20260304-0001',
    transactionType: 'FE',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-03-04',
    fundId: 'MGMT01',
    quantity: 0,
    price: 0,
    amount: 125.00,
    currency: 'USD',
    status: 'D',
    description: 'Quarterly management fee',
  },
  {
    transactionId: '20260305-0001',
    transactionType: 'BU',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-03-05',
    fundId: 'GOOG01',
    quantity: 25.0000,
    price: 172.3000,
    amount: 4307.50,
    currency: 'USD',
    status: 'F',
  },
  {
    transactionId: '20260306-0001',
    transactionType: 'SL',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-06',
    fundId: 'AAPL01',
    quantity: 30.0000,
    price: 180.0000,
    amount: 5400.00,
    currency: 'USD',
    status: 'R',
  },
  {
    transactionId: '20260307-0001',
    transactionType: 'BU',
    accountNumber: '100000006',
    portfolioId: 'PORT0006',
    transactionDate: '2026-03-07',
    fundId: 'AMZN01',
    quantity: 15.0000,
    price: 185.7500,
    amount: 2786.25,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260308-0001',
    transactionType: 'TR',
    accountNumber: '100000007',
    portfolioId: 'PORT0007',
    transactionDate: '2026-03-08',
    fundId: 'BOND03',
    quantity: 500.0000,
    price: 99.0000,
    amount: 49500.00,
    currency: 'USD',
    status: 'D',
    sourceAccount: '100000007',
    destinationAccount: '100000008',
  },
  {
    transactionId: '20260309-0001',
    transactionType: 'FE',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-03-09',
    fundId: 'CUST01',
    quantity: 0,
    price: 0,
    amount: 75.50,
    currency: 'USD',
    status: 'P',
    description: 'Custodian fee',
  },
  {
    transactionId: '20260310-0001',
    transactionType: 'BU',
    accountNumber: '100000008',
    portfolioId: 'PORT0008',
    transactionDate: '2026-03-10',
    fundId: 'TSLA01',
    quantity: 40.0000,
    price: 245.0000,
    amount: 9800.00,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260311-0001',
    transactionType: 'SL',
    accountNumber: '100000009',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-11',
    fundId: 'MSFT02',
    quantity: 75.0000,
    price: 418.0000,
    amount: 31350.00,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260312-0001',
    transactionType: 'BU',
    accountNumber: '100000010',
    portfolioId: 'PORT0003',
    transactionDate: '2026-03-12',
    fundId: 'NVDA01',
    quantity: 20.0000,
    price: 890.5000,
    amount: 17810.00,
    currency: 'USD',
    status: 'F',
  },
  {
    transactionId: '20260313-0001',
    transactionType: 'TR',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-03-13',
    fundId: 'GOOG01',
    quantity: 10.0000,
    price: 174.0000,
    amount: 1740.00,
    currency: 'USD',
    status: 'F',
    sourceAccount: '100000005',
    destinationAccount: '100000006',
  },
  {
    transactionId: '20260314-0001',
    transactionType: 'FE',
    accountNumber: '100000006',
    portfolioId: 'PORT0006',
    transactionDate: '2026-03-14',
    fundId: 'ADVS01',
    quantity: 0,
    price: 0,
    amount: 250.00,
    currency: 'USD',
    status: 'D',
    description: 'Advisory fee - Q1 2026',
  },
  {
    transactionId: '20260315-0001',
    transactionType: 'SL',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-03-15',
    fundId: 'BOND03',
    quantity: 100.0000,
    price: 99.2500,
    amount: 9925.00,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260316-0001',
    transactionType: 'BU',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-03-16',
    fundId: 'META01',
    quantity: 35.0000,
    price: 510.2500,
    amount: 17858.75,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260317-0001',
    transactionType: 'FE',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-17',
    fundId: 'WIRE01',
    quantity: 0,
    price: 0,
    amount: 35.00,
    currency: 'USD',
    status: 'R',
    description: 'Wire transfer fee - reversed',
  },
  {
    transactionId: '20260318-0001',
    transactionType: 'TR',
    accountNumber: '100000009',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-18',
    fundId: 'AAPL01',
    quantity: 50.0000,
    price: 179.0000,
    amount: 8950.00,
    currency: 'USD',
    status: 'R',
    sourceAccount: '100000009',
    destinationAccount: '100000001',
  },
  {
    transactionId: '20260319-0001',
    transactionType: 'SL',
    accountNumber: '100000008',
    portfolioId: 'PORT0008',
    transactionDate: '2026-03-19',
    fundId: 'TSLA01',
    quantity: 20.0000,
    price: 250.5000,
    amount: 5010.00,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260320-0001',
    transactionType: 'BU',
    accountNumber: '100000007',
    portfolioId: 'PORT0007',
    transactionDate: '2026-03-20',
    fundId: 'INTL01',
    quantity: 150.0000,
    price: 52.7500,
    amount: 7912.50,
    currency: 'EUR',
    status: 'D',
  },
];

let transactions: Transaction[] = [...seedTransactions];
let sequenceCounter = seedTransactions.length + 1;

function generateTransactionId(): string {
  const now = new Date();
  const dateStr =
    now.getFullYear().toString() +
    String(now.getMonth() + 1).padStart(2, '0') +
    String(now.getDate()).padStart(2, '0');
  const seq = String(sequenceCounter++).padStart(4, '0');
  return `${dateStr}-${seq}`;
}

export const transactionStore = {
  getAll(): Transaction[] {
    return [...transactions];
  },

  getById(id: string): Transaction | undefined {
    return transactions.find((t) => t.transactionId === id);
  },

  add(
    data: Omit<Transaction, 'transactionId' | 'status'>
  ): Transaction {
    const newTransaction: Transaction = {
      ...data,
      transactionId: generateTransactionId(),
      status: 'P',
    };
    transactions = [newTransaction, ...transactions];
    return newTransaction;
  },

  updateStatus(id: string, status: TransactionStatus): boolean {
    const index = transactions.findIndex((t) => t.transactionId === id);
    if (index === -1) return false;
    transactions[index] = { ...transactions[index], status };
    return true;
  },

  filter(opts: {
    status?: TransactionStatus;
    type?: TransactionType;
    accountNumber?: string;
    dateFrom?: string;
    dateTo?: string;
  }): Transaction[] {
    return transactions.filter((t) => {
      if (opts.status && t.status !== opts.status) return false;
      if (opts.type && t.transactionType !== opts.type) return false;
      if (
        opts.accountNumber &&
        !t.accountNumber.includes(opts.accountNumber)
      )
        return false;
      if (opts.dateFrom && t.transactionDate < opts.dateFrom) return false;
      if (opts.dateTo && t.transactionDate > opts.dateTo) return false;
      return true;
    });
  },

  sort(
    list: Transaction[],
    field: keyof Transaction,
    direction: 'asc' | 'desc'
  ): Transaction[] {
    return [...list].sort((a, b) => {
      const aVal = a[field];
      const bVal = b[field];
      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return direction === 'asc' ? -1 : 1;
      if (bVal == null) return direction === 'asc' ? 1 : -1;
      if (aVal < bVal) return direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return direction === 'asc' ? 1 : -1;
      return 0;
    });
  },
};
