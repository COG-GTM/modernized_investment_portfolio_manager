import { Transaction, TransactionType, TransactionStatus } from '../types/transaction';

/**
 * Seed data: 20 transactions across all types (BU, SL, TR, FE) and statuses (P, D, F, R).
 * Field values match TRNREC.cpy constraints:
 *   - 9-digit account numbers (>= 100000000)
 *   - 8-char alphanumeric portfolio IDs
 *   - 6-char alphanumeric fund IDs
 *   - Proper decimal precision (4 decimal places for quantity/price)
 */
const seedTransactions: Transaction[] = [
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
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
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
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
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
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-03-04',
    fundId: 'GOOG04',
    quantity: 25.0000,
    price: 0.0000,
    amount: 0.0000,
    currency: 'USD',
    status: 'D',
    sourceAccount: '100000004',
    destinationAccount: '100000005',
  },
  {
    transactionId: '20260305-0005',
    transactionType: 'FE',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-03-05',
    fundId: 'FEE001',
    quantity: 0.0000,
    price: 0.0000,
    amount: 75.0000,
    currency: 'USD',
    status: 'D',
    description: 'Annual management fee',
  },
  {
    transactionId: '20260306-0006',
    transactionType: 'BU',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-06',
    fundId: 'AMZN05',
    quantity: 30.0000,
    price: 195.7500,
    amount: 5872.5000,
    currency: 'USD',
    status: 'F',
  },
  {
    transactionId: '20260307-0007',
    transactionType: 'SL',
    accountNumber: '100000006',
    portfolioId: 'PORT0006',
    transactionDate: '2026-03-07',
    fundId: 'TSLA06',
    quantity: 75.0000,
    price: 245.0000,
    amount: 18375.0000,
    currency: 'USD',
    status: 'R',
  },
  {
    transactionId: '20260308-0008',
    transactionType: 'TR',
    accountNumber: '100000007',
    portfolioId: 'PORT0007',
    transactionDate: '2026-03-08',
    fundId: 'NVDA07',
    quantity: 40.0000,
    price: 0.0000,
    amount: 0.0000,
    currency: 'USD',
    status: 'P',
    sourceAccount: '100000007',
    destinationAccount: '100000008',
  },
  {
    transactionId: '20260309-0009',
    transactionType: 'FE',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-03-09',
    fundId: 'FEE001',
    quantity: 0.0000,
    price: 0.0000,
    amount: 150.0000,
    currency: 'USD',
    status: 'F',
    description: 'Wire transfer fee',
  },
  {
    transactionId: '20260310-0010',
    transactionType: 'BU',
    accountNumber: '100000008',
    portfolioId: 'PORT0008',
    transactionDate: '2026-03-10',
    fundId: 'META08',
    quantity: 60.0000,
    price: 510.2500,
    amount: 30615.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260311-0011',
    transactionType: 'SL',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-03-11',
    fundId: 'BOND03',
    quantity: 100.0000,
    price: 99.0000,
    amount: 9900.0000,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260312-0012',
    transactionType: 'BU',
    accountNumber: '100000009',
    portfolioId: 'PORT0009',
    transactionDate: '2026-03-12',
    fundId: 'INTL09',
    quantity: 150.0000,
    price: 52.5000,
    amount: 7875.0000,
    currency: 'EUR',
    status: 'D',
  },
  {
    transactionId: '20260313-0013',
    transactionType: 'TR',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-13',
    fundId: 'AAPL01',
    quantity: 10.0000,
    price: 0.0000,
    amount: 0.0000,
    currency: 'USD',
    status: 'R',
    sourceAccount: '100000001',
    destinationAccount: '100000010',
  },
  {
    transactionId: '20260314-0014',
    transactionType: 'FE',
    accountNumber: '100000010',
    portfolioId: 'PRT00010',
    transactionDate: '2026-03-14',
    fundId: 'FEE001',
    quantity: 0.0000,
    price: 0.0000,
    amount: 25.0000,
    currency: 'USD',
    status: 'P',
    description: 'Account maintenance fee',
  },
  {
    transactionId: '20260315-0015',
    transactionType: 'SL',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-03-15',
    fundId: 'GOOG04',
    quantity: 15.0000,
    price: 178.5000,
    amount: 2677.5000,
    currency: 'USD',
    status: 'F',
  },
  {
    transactionId: '20260316-0016',
    transactionType: 'BU',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-03-16',
    fundId: 'JPMU10',
    quantity: 500.0000,
    price: 22.7500,
    amount: 11375.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260317-0017',
    transactionType: 'TR',
    accountNumber: '100000006',
    portfolioId: 'PORT0006',
    transactionDate: '2026-03-17',
    fundId: 'TSLA06',
    quantity: 20.0000,
    price: 0.0000,
    amount: 0.0000,
    currency: 'USD',
    status: 'D',
    sourceAccount: '100000006',
    destinationAccount: '100000003',
  },
  {
    transactionId: '20260318-0018',
    transactionType: 'FE',
    accountNumber: '100000007',
    portfolioId: 'PORT0007',
    transactionDate: '2026-03-18',
    fundId: 'FEE001',
    quantity: 0.0000,
    price: 0.0000,
    amount: 350.0000,
    currency: 'GBP',
    status: 'R',
    description: 'Custody fee — quarterly',
  },
  {
    transactionId: '20260319-0019',
    transactionType: 'BU',
    accountNumber: '100000008',
    portfolioId: 'PORT0008',
    transactionDate: '2026-03-19',
    fundId: 'VGRD11',
    quantity: 1000.0000,
    price: 35.2500,
    amount: 35250.0000,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260320-0020',
    transactionType: 'SL',
    accountNumber: '100000009',
    portfolioId: 'PORT0009',
    transactionDate: '2026-03-20',
    fundId: 'INTL09',
    quantity: 80.0000,
    price: 53.0000,
    amount: 4240.0000,
    currency: 'EUR',
    status: 'D',
  },
];

let transactions: Transaction[] = [...seedTransactions];
let sequenceCounter = seedTransactions.length;

function generateTransactionId(): string {
  sequenceCounter++;
  const now = new Date();
  const dateStr =
    now.getFullYear().toString() +
    String(now.getMonth() + 1).padStart(2, '0') +
    String(now.getDate()).padStart(2, '0');
  return `${dateStr}-${String(sequenceCounter).padStart(4, '0')}`;
}

export const transactionStore = {
  getAll(): Transaction[] {
    return [...transactions];
  },

  getById(transactionId: string): Transaction | undefined {
    return transactions.find((t) => t.transactionId === transactionId);
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

  updateStatus(transactionId: string, status: TransactionStatus): boolean {
    const idx = transactions.findIndex((t) => t.transactionId === transactionId);
    if (idx === -1) return false;
    transactions[idx] = { ...transactions[idx], status };
    return true;
  },

  filterByStatus(status: TransactionStatus): Transaction[] {
    return transactions.filter((t) => t.status === status);
  },

  filterByType(type: TransactionType): Transaction[] {
    return transactions.filter((t) => t.transactionType === type);
  },

  filterByAccount(accountNumber: string): Transaction[] {
    return transactions.filter((t) => t.accountNumber.includes(accountNumber));
  },

  filterByDateRange(startDate: string, endDate: string): Transaction[] {
    return transactions.filter(
      (t) => t.transactionDate >= startDate && t.transactionDate <= endDate
    );
  },

  sort(field: keyof Transaction, direction: 'asc' | 'desc'): Transaction[] {
    const sorted = [...transactions].sort((a, b) => {
      const aVal = a[field];
      const bVal = b[field];
      if (aVal === undefined && bVal === undefined) return 0;
      if (aVal === undefined) return 1;
      if (bVal === undefined) return -1;
      if (aVal < bVal) return direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return direction === 'asc' ? 1 : -1;
      return 0;
    });
    return sorted;
  },
};
