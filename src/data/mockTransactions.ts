import type { Transaction, TransactionType, TransactionStatus } from '../types/transaction';

/**
 * Mock transaction data seeded with realistic values matching TRNREC.cpy field constraints:
 * - Account numbers: 9-digit strings >= 100000000
 * - Portfolio IDs: 8-char alphanumeric
 * - Fund IDs: 6-char alphanumeric
 * - Quantities/prices: 4 decimal precision (COMP-3)
 */

const SEED_TRANSACTIONS: Transaction[] = [
  // BUY transactions
  {
    transactionId: '20260301-0001',
    transactionType: 'BU',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-01',
    fundId: 'AAPL01',
    quantity: 100.0000,
    price: 178.5000,
    amount: 17850.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260305-0002',
    transactionType: 'BU',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-03-05',
    fundId: 'MSFT02',
    quantity: 50.0000,
    price: 420.2500,
    amount: 21012.5000,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260308-0003',
    transactionType: 'BU',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-03-08',
    fundId: 'GOOG03',
    quantity: 25.0000,
    price: 172.7500,
    amount: 4318.7500,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260310-0004',
    transactionType: 'BU',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-10',
    fundId: 'BOND03',
    quantity: 200.0000,
    price: 98.5000,
    amount: 19700.0000,
    currency: 'USD',
    status: 'F',
  },
  {
    transactionId: '20260312-0005',
    transactionType: 'BU',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-03-12',
    fundId: 'AMZN04',
    quantity: 30.0000,
    price: 185.3000,
    amount: 5559.0000,
    currency: 'USD',
    status: 'P',
  },
  // SELL transactions
  {
    transactionId: '20260302-0006',
    transactionType: 'SL',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-02',
    fundId: 'AAPL01',
    quantity: 50.0000,
    price: 180.2500,
    amount: 9012.5000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260306-0007',
    transactionType: 'SL',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-03-06',
    fundId: 'TSLA05',
    quantity: 75.0000,
    price: 245.0000,
    amount: 18375.0000,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260309-0008',
    transactionType: 'SL',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-03-09',
    fundId: 'GOOG03',
    quantity: 10.0000,
    price: 174.5000,
    amount: 1745.0000,
    currency: 'USD',
    status: 'R',
  },
  {
    transactionId: '20260315-0009',
    transactionType: 'SL',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-03-15',
    fundId: 'NVDA06',
    quantity: 40.0000,
    price: 890.0000,
    amount: 35600.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260318-0010',
    transactionType: 'SL',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-18',
    fundId: 'BOND03',
    quantity: 100.0000,
    price: 99.2500,
    amount: 9925.0000,
    currency: 'USD',
    status: 'F',
  },
  // TRANSFER transactions
  {
    transactionId: '20260303-0011',
    transactionType: 'TR',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-03',
    fundId: 'AAPL01',
    quantity: 25.0000,
    price: 0.0000,
    amount: 0.0000,
    currency: 'USD',
    status: 'D',
    sourceAccount: '100000001',
    destinationAccount: '100000002',
  },
  {
    transactionId: '20260307-0012',
    transactionType: 'TR',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-03-07',
    fundId: 'MSFT02',
    quantity: 15.0000,
    price: 0.0000,
    amount: 0.0000,
    currency: 'USD',
    status: 'P',
    sourceAccount: '100000003',
    destinationAccount: '100000004',
  },
  {
    transactionId: '20260311-0013',
    transactionType: 'TR',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-03-11',
    fundId: 'BOND03',
    quantity: 50.0000,
    price: 0.0000,
    amount: 0.0000,
    currency: 'USD',
    status: 'R',
    sourceAccount: '100000004',
    destinationAccount: '100000005',
  },
  {
    transactionId: '20260320-0014',
    transactionType: 'TR',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-03-20',
    fundId: 'GOOG03',
    quantity: 20.0000,
    price: 0.0000,
    amount: 0.0000,
    currency: 'USD',
    status: 'D',
    sourceAccount: '100000002',
    destinationAccount: '100000001',
  },
  {
    transactionId: '20260322-0015',
    transactionType: 'TR',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-03-22',
    fundId: 'NVDA06',
    quantity: 10.0000,
    price: 0.0000,
    amount: 0.0000,
    currency: 'USD',
    status: 'F',
    sourceAccount: '100000005',
    destinationAccount: '100000003',
  },
  // FEE transactions
  {
    transactionId: '20260304-0016',
    transactionType: 'FE',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-04',
    fundId: 'FEE001',
    quantity: 0.0000,
    price: 0.0000,
    amount: 25.0000,
    currency: 'USD',
    status: 'D',
    description: 'Monthly account maintenance fee',
  },
  {
    transactionId: '20260314-0017',
    transactionType: 'FE',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-03-14',
    fundId: 'FEE001',
    quantity: 0.0000,
    price: 0.0000,
    amount: 50.0000,
    currency: 'USD',
    status: 'P',
    description: 'Wire transfer fee',
  },
  {
    transactionId: '20260316-0018',
    transactionType: 'FE',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-03-16',
    fundId: 'FEE002',
    quantity: 0.0000,
    price: 0.0000,
    amount: 75.0000,
    currency: 'EUR',
    status: 'D',
    description: 'Annual advisory fee',
  },
  {
    transactionId: '20260319-0019',
    transactionType: 'FE',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-03-19',
    fundId: 'FEE001',
    quantity: 0.0000,
    price: 0.0000,
    amount: 15.0000,
    currency: 'USD',
    status: 'F',
    description: 'Late payment penalty',
  },
  {
    transactionId: '20260321-0020',
    transactionType: 'FE',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-03-21',
    fundId: 'FEE002',
    quantity: 0.0000,
    price: 0.0000,
    amount: 100.0000,
    currency: 'GBP',
    status: 'R',
    description: 'Custody fee — reversed per client request',
  },
];

let sequenceCounter = 21;

function getNextSequence(): string {
  return String(sequenceCounter++).padStart(4, '0');
}

function generateTransactionId(): string {
  const now = new Date();
  const dateStr = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0'),
  ].join('');
  return `${dateStr}-${getNextSequence()}`;
}

type SortDirection = 'asc' | 'desc';

class TransactionStore {
  private transactions: Transaction[];

  constructor(seed: Transaction[]) {
    this.transactions = [...seed];
  }

  getAll(): Transaction[] {
    return [...this.transactions];
  }

  getById(transactionId: string): Transaction | undefined {
    return this.transactions.find((t) => t.transactionId === transactionId);
  }

  add(data: Omit<Transaction, 'transactionId' | 'status'>, transactionId?: string): Transaction {
    const transaction: Transaction = {
      ...data,
      transactionId: transactionId || generateTransactionId(),
      status: 'P',
    };
    this.transactions.unshift(transaction);
    return transaction;
  }

  updateStatus(transactionId: string, status: TransactionStatus): boolean {
    const idx = this.transactions.findIndex((t) => t.transactionId === transactionId);
    if (idx === -1) return false;
    this.transactions[idx] = { ...this.transactions[idx], status };
    return true;
  }

  filter(criteria: {
    status?: TransactionStatus;
    type?: TransactionType;
    accountNumber?: string;
    dateFrom?: string;
    dateTo?: string;
  }): Transaction[] {
    return this.transactions.filter((t) => {
      if (criteria.status && t.status !== criteria.status) return false;
      if (criteria.type && t.transactionType !== criteria.type) return false;
      if (criteria.accountNumber && !t.accountNumber.includes(criteria.accountNumber)) return false;
      if (criteria.dateFrom && t.transactionDate < criteria.dateFrom) return false;
      if (criteria.dateTo && t.transactionDate > criteria.dateTo) return false;
      return true;
    });
  }

  sort(transactions: Transaction[], field: keyof Transaction, direction: SortDirection): Transaction[] {
    const sorted = [...transactions];
    sorted.sort((a, b) => {
      const aVal = a[field];
      const bVal = b[field];
      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return direction === 'asc' ? -1 : 1;
      if (bVal == null) return direction === 'asc' ? 1 : -1;
      if (aVal < bVal) return direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return direction === 'asc' ? 1 : -1;
      return 0;
    });
    return sorted;
  }
}

export const transactionStore = new TransactionStore(SEED_TRANSACTIONS);
export { generateTransactionId };
