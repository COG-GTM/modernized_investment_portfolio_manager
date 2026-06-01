import { Transaction, TransactionType, TransactionStatus } from '../types/transaction';

const SEED_TRANSACTIONS: Transaction[] = [
  {
    transactionId: '20260401-0001',
    transactionType: 'BU',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-04-01',
    fundId: 'AAPL01',
    quantity: 150.0000,
    price: 178.5000,
    amount: 26775.0000,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260401-0002',
    transactionType: 'SL',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-04-01',
    fundId: 'MSFT02',
    quantity: 75.0000,
    price: 420.2500,
    amount: 31518.7500,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260401-0003',
    transactionType: 'TR',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-04-01',
    fundId: 'BOND03',
    quantity: 500.0000,
    price: 100.0000,
    amount: 50000.0000,
    currency: 'USD',
    status: 'P',
    sourceAccount: '100000003',
    destinationAccount: '100000004',
  },
  {
    transactionId: '20260401-0004',
    transactionType: 'FE',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-04-01',
    fundId: '',
    quantity: 0,
    price: 0,
    amount: 49.9900,
    currency: 'USD',
    status: 'D',
    description: 'Quarterly management fee',
  },
  {
    transactionId: '20260402-0001',
    transactionType: 'BU',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-04-02',
    fundId: 'GOOG01',
    quantity: 25.0000,
    price: 165.7500,
    amount: 4143.7500,
    currency: 'USD',
    status: 'F',
  },
  {
    transactionId: '20260402-0002',
    transactionType: 'SL',
    accountNumber: '100000006',
    portfolioId: 'PORT0006',
    transactionDate: '2026-04-02',
    fundId: 'AMZN01',
    quantity: 100.0000,
    price: 185.3000,
    amount: 18530.0000,
    currency: 'USD',
    status: 'R',
  },
  {
    transactionId: '20260402-0003',
    transactionType: 'TR',
    accountNumber: '100000007',
    portfolioId: 'PORT0007',
    transactionDate: '2026-04-02',
    fundId: 'TSLA01',
    quantity: 200.0000,
    price: 250.0000,
    amount: 50000.0000,
    currency: 'USD',
    status: 'D',
    sourceAccount: '100000007',
    destinationAccount: '100000008',
  },
  {
    transactionId: '20260403-0001',
    transactionType: 'BU',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-04-03',
    fundId: 'NVDA01',
    quantity: 50.0000,
    price: 875.0000,
    amount: 43750.0000,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260403-0002',
    transactionType: 'FE',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-04-03',
    fundId: '',
    quantity: 0,
    price: 0,
    amount: 125.0000,
    currency: 'USD',
    status: 'P',
    description: 'Annual custodial fee',
  },
  {
    transactionId: '20260403-0003',
    transactionType: 'SL',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-04-03',
    fundId: 'META01',
    quantity: 300.0000,
    price: 505.7500,
    amount: 151725.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260404-0001',
    transactionType: 'BU',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-04-04',
    fundId: 'JPM001',
    quantity: 80.0000,
    price: 198.5000,
    amount: 15880.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260404-0002',
    transactionType: 'TR',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-04-04',
    fundId: 'AAPL01',
    quantity: 50.0000,
    price: 179.0000,
    amount: 8950.0000,
    currency: 'USD',
    status: 'F',
    sourceAccount: '100000001',
    destinationAccount: '100000009',
  },
  {
    transactionId: '20260405-0001',
    transactionType: 'SL',
    accountNumber: '100000008',
    portfolioId: 'PORT0008',
    transactionDate: '2026-04-05',
    fundId: 'INTC01',
    quantity: 1000.0000,
    price: 32.2500,
    amount: 32250.0000,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260405-0002',
    transactionType: 'FE',
    accountNumber: '100000006',
    portfolioId: 'PORT0006',
    transactionDate: '2026-04-05',
    fundId: '',
    quantity: 0,
    price: 0,
    amount: 75.0000,
    currency: 'USD',
    status: 'R',
    description: 'Wire transfer fee',
  },
  {
    transactionId: '20260406-0001',
    transactionType: 'BU',
    accountNumber: '100000009',
    portfolioId: 'PORT0009',
    transactionDate: '2026-04-06',
    fundId: 'DIS001',
    quantity: 120.0000,
    price: 112.7500,
    amount: 13530.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260406-0002',
    transactionType: 'BU',
    accountNumber: '100000010',
    portfolioId: 'PRT00010',
    transactionDate: '2026-04-06',
    fundId: 'V00001',
    quantity: 60.0000,
    price: 275.5000,
    amount: 16530.0000,
    currency: 'USD',
    status: 'F',
  },
  {
    transactionId: '20260407-0001',
    transactionType: 'SL',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-04-07',
    fundId: 'BA0001',
    quantity: 45.0000,
    price: 210.0000,
    amount: 9450.0000,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260407-0002',
    transactionType: 'TR',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-04-07',
    fundId: 'MSFT02',
    quantity: 30.0000,
    price: 422.0000,
    amount: 12660.0000,
    currency: 'USD',
    status: 'R',
    sourceAccount: '100000002',
    destinationAccount: '100000005',
  },
  {
    transactionId: '20260408-0001',
    transactionType: 'FE',
    accountNumber: '100000007',
    portfolioId: 'PORT0007',
    transactionDate: '2026-04-08',
    fundId: '',
    quantity: 0,
    price: 0,
    amount: 250.0000,
    currency: 'USD',
    status: 'D',
    description: 'Advisory fee — Q1 2026',
  },
  {
    transactionId: '20260408-0002',
    transactionType: 'BU',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-04-08',
    fundId: 'BOND03',
    quantity: 1000.0000,
    price: 99.7500,
    amount: 99750.0000,
    currency: 'USD',
    status: 'P',
  },
];

let transactions: Transaction[] = [...SEED_TRANSACTIONS];
let sequenceCounter = SEED_TRANSACTIONS.length + 1;

function generateTransactionId(): string {
  const now = new Date();
  const dateStr = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0'),
  ].join('');
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
    const idx = transactions.findIndex((t) => t.transactionId === id);
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

  filterByAccount(account: string): Transaction[] {
    return transactions.filter((t) => t.accountNumber.includes(account));
  },

  filterByDateRange(start: string, end: string): Transaction[] {
    return transactions.filter(
      (t) => t.transactionDate >= start && t.transactionDate <= end
    );
  },

  sort(
    field: keyof Transaction,
    direction: 'asc' | 'desc' = 'asc'
  ): Transaction[] {
    const sorted = [...transactions].sort((a, b) => {
      const aVal = a[field];
      const bVal = b[field];
      if (aVal === undefined || bVal === undefined) return 0;
      if (aVal < bVal) return direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return direction === 'asc' ? 1 : -1;
      return 0;
    });
    return sorted;
  },
};
