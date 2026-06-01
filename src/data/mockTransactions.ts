import type { Transaction, TransactionType, TransactionStatus } from '../types/transaction';

/**
 * Mock transaction data seeded with realistic values matching TRNREC.cpy field constraints:
 * - Account numbers: 9-digit strings (PIC 9(9)), >= 100000000
 * - Portfolio IDs: 8-char alphanumeric (PIC X(8))
 * - Fund IDs: 6-char alphanumeric (PIC X(6))
 * - Quantity/Price: 4 decimal places (COMP-3)
 * - Currency: 3-char ISO (PIC X(3))
 */

const SEED_TRANSACTIONS: Transaction[] = [
  // BUY transactions
  {
    transactionId: '20260315-0001',
    transactionType: 'BU',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-15',
    fundId: 'AAPL01',
    quantity: 100.0000,
    price: 178.5200,
    amount: 17852.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260316-0002',
    transactionType: 'BU',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-03-16',
    fundId: 'MSFT02',
    quantity: 50.0000,
    price: 415.3000,
    amount: 20765.0000,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260317-0003',
    transactionType: 'BU',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-03-17',
    fundId: 'GOOG03',
    quantity: 25.0000,
    price: 172.8400,
    amount: 4321.0000,
    currency: 'USD',
    status: 'F',
  },
  {
    transactionId: '20260318-0004',
    transactionType: 'BU',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-03-18',
    fundId: 'AMZN04',
    quantity: 200.0000,
    price: 185.6700,
    amount: 37134.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260319-0005',
    transactionType: 'BU',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-03-19',
    fundId: 'TSLA05',
    quantity: 75.0000,
    price: 245.1000,
    amount: 18382.5000,
    currency: 'USD',
    status: 'P',
  },
  // SELL transactions
  {
    transactionId: '20260315-0006',
    transactionType: 'SL',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-15',
    fundId: 'BOND03',
    quantity: 500.0000,
    price: 98.7500,
    amount: 49375.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260316-0007',
    transactionType: 'SL',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-03-16',
    fundId: 'AAPL01',
    quantity: 30.0000,
    price: 179.2000,
    amount: 5376.0000,
    currency: 'USD',
    status: 'R',
  },
  {
    transactionId: '20260317-0008',
    transactionType: 'SL',
    accountNumber: '100000006',
    portfolioId: 'PORT0006',
    transactionDate: '2026-03-17',
    fundId: 'META06',
    quantity: 60.0000,
    price: 510.4500,
    amount: 30627.0000,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260318-0009',
    transactionType: 'SL',
    accountNumber: '100000007',
    portfolioId: 'PORT0007',
    transactionDate: '2026-03-18',
    fundId: 'NVDA07',
    quantity: 40.0000,
    price: 890.2000,
    amount: 35608.0000,
    currency: 'USD',
    status: 'F',
  },
  {
    transactionId: '20260319-0010',
    transactionType: 'SL',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-03-19',
    fundId: 'GOOG03',
    quantity: 10.0000,
    price: 173.5000,
    amount: 1735.0000,
    currency: 'USD',
    status: 'D',
  },
  // TRANSFER transactions
  {
    transactionId: '20260315-0011',
    transactionType: 'TR',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-15',
    fundId: 'AAPL01',
    quantity: 50.0000,
    price: 178.5200,
    amount: 8926.0000,
    currency: 'USD',
    status: 'D',
    sourceAccount: '100000001',
    destinationAccount: '100000002',
  },
  {
    transactionId: '20260316-0012',
    transactionType: 'TR',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-03-16',
    fundId: 'MSFT02',
    quantity: 20.0000,
    price: 415.3000,
    amount: 8306.0000,
    currency: 'USD',
    status: 'P',
    sourceAccount: '100000004',
    destinationAccount: '100000005',
  },
  {
    transactionId: '20260317-0013',
    transactionType: 'TR',
    accountNumber: '100000006',
    portfolioId: 'PORT0006',
    transactionDate: '2026-03-17',
    fundId: 'BOND03',
    quantity: 100.0000,
    price: 98.7500,
    amount: 9875.0000,
    currency: 'USD',
    status: 'R',
    sourceAccount: '100000006',
    destinationAccount: '100000007',
  },
  {
    transactionId: '20260318-0014',
    transactionType: 'TR',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-03-18',
    fundId: 'TSLA05',
    quantity: 15.0000,
    price: 245.1000,
    amount: 3676.5000,
    currency: 'USD',
    status: 'F',
    sourceAccount: '100000003',
    destinationAccount: '100000008',
  },
  {
    transactionId: '20260319-0015',
    transactionType: 'TR',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-03-19',
    fundId: 'AMZN04',
    quantity: 30.0000,
    price: 185.6700,
    amount: 5570.1000,
    currency: 'USD',
    status: 'D',
    sourceAccount: '100000005',
    destinationAccount: '100000001',
  },
  // FEE transactions
  {
    transactionId: '20260315-0016',
    transactionType: 'FE',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-15',
    fundId: 'FEE001',
    quantity: 0,
    price: 0,
    amount: 25.0000,
    currency: 'USD',
    status: 'D',
    description: 'Quarterly management fee',
  },
  {
    transactionId: '20260316-0017',
    transactionType: 'FE',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-03-16',
    fundId: 'FEE001',
    quantity: 0,
    price: 0,
    amount: 50.0000,
    currency: 'USD',
    status: 'P',
    description: 'Annual custodian fee',
  },
  {
    transactionId: '20260317-0018',
    transactionType: 'FE',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-03-17',
    fundId: 'FEE001',
    quantity: 0,
    price: 0,
    amount: 15.5000,
    currency: 'USD',
    status: 'F',
    description: 'Wire transfer fee',
  },
  {
    transactionId: '20260318-0019',
    transactionType: 'FE',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-03-18',
    fundId: 'FEE001',
    quantity: 0,
    price: 0,
    amount: 100.0000,
    currency: 'USD',
    status: 'R',
    description: 'Account maintenance fee — reversed per client request',
  },
  {
    transactionId: '20260319-0020',
    transactionType: 'FE',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-03-19',
    fundId: 'FEE001',
    quantity: 0,
    price: 0,
    amount: 75.0000,
    currency: 'USD',
    status: 'D',
    description: 'Portfolio rebalancing fee',
  },
];

/** Sequence counter for generating new transaction IDs */
let sequenceCounter = 21;

/** In-memory transaction store — no localStorage, no backend API */
class TransactionStore {
  private transactions: Transaction[];

  constructor() {
    this.transactions = [...SEED_TRANSACTIONS];
  }

  getAll(): Transaction[] {
    return [...this.transactions];
  }

  getById(transactionId: string): Transaction | undefined {
    return this.transactions.find((t) => t.transactionId === transactionId);
  }

  add(transaction: Transaction): Transaction {
    this.transactions.unshift(transaction);
    return transaction;
  }

  updateStatus(transactionId: string, status: TransactionStatus): boolean {
    const idx = this.transactions.findIndex((t) => t.transactionId === transactionId);
    if (idx === -1) return false;
    this.transactions[idx] = { ...this.transactions[idx], status };
    return true;
  }

  filterByStatus(status: TransactionStatus): Transaction[] {
    return this.transactions.filter((t) => t.status === status);
  }

  filterByType(type: TransactionType): Transaction[] {
    return this.transactions.filter((t) => t.transactionType === type);
  }

  filterByAccount(accountNumber: string): Transaction[] {
    return this.transactions.filter((t) => t.accountNumber.includes(accountNumber));
  }

  filterByDateRange(startDate: string, endDate: string): Transaction[] {
    return this.transactions.filter(
      (t) => t.transactionDate >= startDate && t.transactionDate <= endDate,
    );
  }

  /** Generate a new transaction ID in YYYYMMDD-NNNN format */
  generateId(): string {
    const now = new Date();
    const dateStr =
      now.getFullYear().toString() +
      (now.getMonth() + 1).toString().padStart(2, '0') +
      now.getDate().toString().padStart(2, '0');
    const seq = (sequenceCounter++).toString().padStart(4, '0');
    return `${dateStr}-${seq}`;
  }
}

/** Singleton store instance */
export const transactionStore = new TransactionStore();
