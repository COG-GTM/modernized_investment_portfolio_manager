import { Transaction, TransactionType, TransactionStatus } from '../types/transaction';

// Seed data: 20 transactions across all types and statuses, matching TRNREC.cpy field constraints
const seedTransactions: Transaction[] = [
  // BUY transactions
  {
    transactionId: '20260301-0001',
    transactionType: 'BU',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-01',
    fundId: 'AAPL01',
    quantity: 150.0000,
    price: 178.5200,
    amount: 26778.0000,
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
    quantity: 75.0000,
    price: 415.3000,
    amount: 31147.5000,
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
    quantity: 50.0000,
    price: 172.8000,
    amount: 8640.0000,
    currency: 'USD',
    status: 'F',
  },
  {
    transactionId: '20260310-0004',
    transactionType: 'BU',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-03-10',
    fundId: 'AMZN04',
    quantity: 200.0000,
    price: 186.2500,
    amount: 37250.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260312-0005',
    transactionType: 'BU',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-12',
    fundId: 'BOND03',
    quantity: 500.0000,
    price: 98.7500,
    amount: 49375.0000,
    currency: 'USD',
    status: 'P',
  },

  // SELL transactions
  {
    transactionId: '20260302-0006',
    transactionType: 'SL',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-03-02',
    fundId: 'AAPL01',
    quantity: 100.0000,
    price: 179.1000,
    amount: 17910.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260306-0007',
    transactionType: 'SL',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-03-06',
    fundId: 'TSLA05',
    quantity: 30.0000,
    price: 245.6000,
    amount: 7368.0000,
    currency: 'USD',
    status: 'R',
  },
  {
    transactionId: '20260311-0008',
    transactionType: 'SL',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-03-11',
    fundId: 'NVDA06',
    quantity: 25.0000,
    price: 890.4000,
    amount: 22260.0000,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260315-0009',
    transactionType: 'SL',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-15',
    fundId: 'MSFT02',
    quantity: 60.0000,
    price: 418.0000,
    amount: 25080.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260318-0010',
    transactionType: 'SL',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-03-18',
    fundId: 'BOND03',
    quantity: 250.0000,
    price: 99.1200,
    amount: 24780.0000,
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
    quantity: 50.0000,
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
    fundId: 'GOOG03',
    quantity: 20.0000,
    price: 0.0000,
    amount: 0.0000,
    currency: 'USD',
    status: 'P',
    sourceAccount: '100000003',
    destinationAccount: '100000004',
  },
  {
    transactionId: '20260313-0013',
    transactionType: 'TR',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-03-13',
    fundId: 'MSFT02',
    quantity: 40.0000,
    price: 0.0000,
    amount: 0.0000,
    currency: 'USD',
    status: 'F',
    sourceAccount: '100000005',
    destinationAccount: '100000001',
  },
  {
    transactionId: '20260319-0014',
    transactionType: 'TR',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-03-19',
    fundId: 'AMZN04',
    quantity: 80.0000,
    price: 0.0000,
    amount: 0.0000,
    currency: 'USD',
    status: 'D',
    sourceAccount: '100000002',
    destinationAccount: '100000003',
  },
  {
    transactionId: '20260322-0015',
    transactionType: 'TR',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-03-22',
    fundId: 'TSLA05',
    quantity: 15.0000,
    price: 0.0000,
    amount: 0.0000,
    currency: 'USD',
    status: 'R',
    sourceAccount: '100000004',
    destinationAccount: '100000005',
  },

  // FEE transactions
  {
    transactionId: '20260304-0016',
    transactionType: 'FE',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-03-04',
    fundId: '',
    quantity: 0.0000,
    price: 0.0000,
    amount: 25.0000,
    currency: 'USD',
    status: 'D',
    description: 'Quarterly management fee',
  },
  {
    transactionId: '20260309-0017',
    transactionType: 'FE',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-03-09',
    fundId: '',
    quantity: 0.0000,
    price: 0.0000,
    amount: 50.0000,
    currency: 'USD',
    status: 'P',
    description: 'Annual custodian fee',
  },
  {
    transactionId: '20260314-0018',
    transactionType: 'FE',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-03-14',
    fundId: '',
    quantity: 0.0000,
    price: 0.0000,
    amount: 15.5000,
    currency: 'USD',
    status: 'F',
    description: 'Wire transfer fee',
  },
  {
    transactionId: '20260320-0019',
    transactionType: 'FE',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-03-20',
    fundId: '',
    quantity: 0.0000,
    price: 0.0000,
    amount: 75.0000,
    currency: 'USD',
    status: 'D',
    description: 'Account maintenance fee',
  },
  {
    transactionId: '20260325-0020',
    transactionType: 'FE',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-03-25',
    fundId: '',
    quantity: 0.0000,
    price: 0.0000,
    amount: 100.0000,
    currency: 'USD',
    status: 'R',
    description: 'Advisory service fee — reversed per client request',
  },
];

// In-memory transaction store
let transactions: Transaction[] = [...seedTransactions];
let sequenceCounter = 21; // next sequence after seed data

class TransactionStore {
  getAll(): Transaction[] {
    return [...transactions];
  }

  getById(transactionId: string): Transaction | undefined {
    return transactions.find(t => t.transactionId === transactionId);
  }

  add(transaction: Transaction): Transaction {
    transactions = [transaction, ...transactions];
    return transaction;
  }

  updateStatus(transactionId: string, status: TransactionStatus): Transaction | undefined {
    const index = transactions.findIndex(t => t.transactionId === transactionId);
    if (index === -1) return undefined;
    transactions[index] = { ...transactions[index], status };
    return transactions[index];
  }

  generateTransactionId(): string {
    const now = new Date();
    const dateStr = now.getFullYear().toString() +
      String(now.getMonth() + 1).padStart(2, '0') +
      String(now.getDate()).padStart(2, '0');
    const seq = String(sequenceCounter++).padStart(4, '0');
    return `${dateStr}-${seq}`;
  }

  filterByStatus(status: TransactionStatus): Transaction[] {
    return transactions.filter(t => t.status === status);
  }

  filterByType(type: TransactionType): Transaction[] {
    return transactions.filter(t => t.transactionType === type);
  }

  filterByAccount(accountNumber: string): Transaction[] {
    return transactions.filter(t => t.accountNumber.includes(accountNumber));
  }

  filterByDateRange(startDate: string, endDate: string): Transaction[] {
    return transactions.filter(t => t.transactionDate >= startDate && t.transactionDate <= endDate);
  }

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
  }
}

export const transactionStore = new TransactionStore();
