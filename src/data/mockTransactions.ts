import type { Transaction, TransactionType, TransactionStatus } from '../types/transaction';

/**
 * Mock transaction data seeded with 20 transactions across all types and statuses.
 * Field values match TRNREC.cpy constraints:
 * - 9-digit account numbers (>= 100000000)
 * - 8-char portfolio IDs
 * - 6-char fund IDs
 * - Proper decimal precision (4 places for quantity/price)
 */
const SEED_TRANSACTIONS: Transaction[] = [
  {
    transactionId: '20260301-0001',
    transactionType: 'BU',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-01',
    fundId: 'AAPL01',
    quantity: 100.0000,
    price: 185.5000,
    amount: 18550.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260302-0002',
    transactionType: 'SL',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-02',
    fundId: 'MSFT02',
    quantity: 50.0000,
    price: 420.2500,
    amount: 21012.5000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260303-0003',
    transactionType: 'BU',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-03-03',
    fundId: 'BOND03',
    quantity: 200.0000,
    price: 98.7500,
    amount: 19750.0000,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260304-0004',
    transactionType: 'TR',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-03-04',
    fundId: 'GOOG04',
    quantity: 25.0000,
    price: 175.0000,
    amount: 4375.0000,
    currency: 'USD',
    status: 'D',
    sourceAccount: '100000003',
    destinationAccount: '100000004',
  },
  {
    transactionId: '20260305-0005',
    transactionType: 'FE',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-05',
    fundId: 'MGMT05',
    quantity: 0,
    price: 0,
    amount: 125.0000,
    currency: 'USD',
    status: 'D',
    description: 'Quarterly management fee',
  },
  {
    transactionId: '20260306-0006',
    transactionType: 'BU',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-03-06',
    fundId: 'AMZN06',
    quantity: 30.0000,
    price: 195.3000,
    amount: 5859.0000,
    currency: 'USD',
    status: 'F',
  },
  {
    transactionId: '20260307-0007',
    transactionType: 'SL',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-03-07',
    fundId: 'TSLA07',
    quantity: 75.0000,
    price: 250.0000,
    amount: 18750.0000,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260308-0008',
    transactionType: 'TR',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-03-08',
    fundId: 'AAPL01',
    quantity: 10.0000,
    price: 185.5000,
    amount: 1855.0000,
    currency: 'USD',
    status: 'R',
    sourceAccount: '100000005',
    destinationAccount: '100000001',
  },
  {
    transactionId: '20260309-0009',
    transactionType: 'FE',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-03-09',
    fundId: 'CUST08',
    quantity: 0,
    price: 0,
    amount: 50.0000,
    currency: 'USD',
    status: 'P',
    description: 'Custodian fee',
  },
  {
    transactionId: '20260310-0010',
    transactionType: 'BU',
    accountNumber: '100000006',
    portfolioId: 'PORT0006',
    transactionDate: '2026-03-10',
    fundId: 'NVDA09',
    quantity: 40.0000,
    price: 890.0000,
    amount: 35600.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260311-0011',
    transactionType: 'SL',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-03-11',
    fundId: 'AMZN06',
    quantity: 15.0000,
    price: 198.7500,
    amount: 2981.2500,
    currency: 'USD',
    status: 'F',
  },
  {
    transactionId: '20260312-0012',
    transactionType: 'BU',
    accountNumber: '100000007',
    portfolioId: 'PORT0007',
    transactionDate: '2026-03-12',
    fundId: 'BOND03',
    quantity: 500.0000,
    price: 99.0000,
    amount: 49500.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260313-0013',
    transactionType: 'TR',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-03-13',
    fundId: 'MSFT02',
    quantity: 20.0000,
    price: 422.0000,
    amount: 8440.0000,
    currency: 'EUR',
    status: 'P',
    sourceAccount: '100000002',
    destinationAccount: '100000007',
  },
  {
    transactionId: '20260314-0014',
    transactionType: 'FE',
    accountNumber: '100000006',
    portfolioId: 'PORT0006',
    transactionDate: '2026-03-14',
    fundId: 'ADVS10',
    quantity: 0,
    price: 0,
    amount: 250.0000,
    currency: 'USD',
    status: 'D',
    description: 'Advisory fee',
  },
  {
    transactionId: '20260315-0015',
    transactionType: 'SL',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-15',
    fundId: 'AAPL01',
    quantity: 50.0000,
    price: 188.0000,
    amount: 9400.0000,
    currency: 'USD',
    status: 'R',
  },
  {
    transactionId: '20260316-0016',
    transactionType: 'BU',
    accountNumber: '100000008',
    portfolioId: 'PORT0008',
    transactionDate: '2026-03-16',
    fundId: 'META11',
    quantity: 60.0000,
    price: 505.5000,
    amount: 30330.0000,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260317-0017',
    transactionType: 'TR',
    accountNumber: '100000008',
    portfolioId: 'PORT0008',
    transactionDate: '2026-03-17',
    fundId: 'META11',
    quantity: 30.0000,
    price: 505.5000,
    amount: 15165.0000,
    currency: 'USD',
    status: 'F',
    sourceAccount: '100000008',
    destinationAccount: '100000003',
  },
  {
    transactionId: '20260318-0018',
    transactionType: 'FE',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-03-18',
    fundId: 'WIRE12',
    quantity: 0,
    price: 0,
    amount: 35.0000,
    currency: 'USD',
    status: 'R',
    description: 'Wire transfer fee',
  },
  {
    transactionId: '20260319-0019',
    transactionType: 'BU',
    accountNumber: '100000009',
    portfolioId: 'PORT0009',
    transactionDate: '2026-03-19',
    fundId: 'GOOG04',
    quantity: 80.0000,
    price: 176.2500,
    amount: 14100.0000,
    currency: 'GBP',
    status: 'D',
  },
  {
    transactionId: '20260320-0020',
    transactionType: 'SL',
    accountNumber: '100000009',
    portfolioId: 'PORT0009',
    transactionDate: '2026-03-20',
    fundId: 'NVDA09',
    quantity: 10.0000,
    price: 895.0000,
    amount: 8950.0000,
    currency: 'GBP',
    status: 'P',
  },
];

let transactions: Transaction[] = [...SEED_TRANSACTIONS];
let sequenceCounter = SEED_TRANSACTIONS.length;

export function generateTransactionId(): string {
  sequenceCounter++;
  const now = new Date();
  const dateStr = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0'),
  ].join('');
  return `${dateStr}-${String(sequenceCounter).padStart(4, '0')}`;
}

export const transactionStore = {
  getAll(): Transaction[] {
    return [...transactions];
  },

  getById(id: string): Transaction | undefined {
    return transactions.find((t) => t.transactionId === id);
  },

  add(
    data: Omit<Transaction, 'status'> | Omit<Transaction, 'transactionId' | 'status'>
  ): Transaction {
    const newTransaction: Transaction = {
      ...data,
      transactionId: 'transactionId' in data ? data.transactionId : generateTransactionId(),
      status: 'P',
    };
    transactions = [newTransaction, ...transactions];
    return newTransaction;
  },

  updateStatus(id: string, status: TransactionStatus): boolean {
    const index = transactions.findIndex((t) => t.transactionId === id);
    if (index === -1) return false;
    transactions = transactions.map((t) =>
      t.transactionId === id ? { ...t, status } : t
    );
    return true;
  },

  filter(opts: {
    status?: TransactionStatus;
    accountNumber?: string;
    type?: TransactionType;
    dateFrom?: string;
    dateTo?: string;
  }): Transaction[] {
    return transactions.filter((t) => {
      if (opts.status && t.status !== opts.status) return false;
      if (opts.accountNumber && !t.accountNumber.includes(opts.accountNumber))
        return false;
      if (opts.type && t.transactionType !== opts.type) return false;
      if (opts.dateFrom && t.transactionDate < opts.dateFrom) return false;
      if (opts.dateTo && t.transactionDate > opts.dateTo) return false;
      return true;
    });
  },

  sort(
    list: Transaction[],
    field: keyof Transaction,
    direction: 'asc' | 'desc' = 'asc'
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
