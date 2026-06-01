import { Transaction, TransactionType, TransactionStatus } from '../types/transaction';

const seedTransactions: Transaction[] = [
  {
    transactionId: '20260101-0001',
    transactionType: 'BU',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-01-01',
    fundId: 'AAPL01',
    quantity: 100.0000,
    price: 185.5000,
    amount: 18550.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260102-0002',
    transactionType: 'SL',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-01-02',
    fundId: 'MSFT02',
    quantity: 50.0000,
    price: 420.2500,
    amount: 21012.5000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260103-0003',
    transactionType: 'TR',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-01-03',
    fundId: 'BOND03',
    quantity: 200.0000,
    price: 0.0000,
    amount: 0.0000,
    currency: 'USD',
    status: 'P',
    sourceAccount: '100000003',
    destinationAccount: '100000004',
  },
  {
    transactionId: '20260104-0004',
    transactionType: 'FE',
    accountNumber: '100000004',
    portfolioId: 'PORT0004',
    transactionDate: '2026-01-04',
    fundId: '',
    quantity: 0.0000,
    price: 0.0000,
    amount: 25.0000,
    currency: 'USD',
    status: 'D',
    description: 'Annual management fee',
  },
  {
    transactionId: '20260105-0005',
    transactionType: 'BU',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-01-05',
    fundId: 'GOOG01',
    quantity: 30.0000,
    price: 175.3000,
    amount: 5259.0000,
    currency: 'USD',
    status: 'F',
  },
  {
    transactionId: '20260106-0006',
    transactionType: 'SL',
    accountNumber: '100000001',
    portfolioId: 'PORT0001',
    transactionDate: '2026-01-06',
    fundId: 'AMZN01',
    quantity: 20.0000,
    price: 195.7500,
    amount: 3915.0000,
    currency: 'USD',
    status: 'R',
  },
  {
    transactionId: '20260107-0007',
    transactionType: 'BU',
    accountNumber: '100000002',
    portfolioId: 'PORT0002',
    transactionDate: '2026-01-07',
    fundId: 'TSLA01',
    quantity: 75.0000,
    price: 250.0000,
    amount: 18750.0000,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260108-0008',
    transactionType: 'TR',
    accountNumber: '100000005',
    portfolioId: 'PORT0005',
    transactionDate: '2026-01-08',
    fundId: 'AAPL01',
    quantity: 50.0000,
    price: 0.0000,
    amount: 0.0000,
    currency: 'USD',
    status: 'D',
    sourceAccount: '100000005',
    destinationAccount: '100000001',
  },
  {
    transactionId: '20260109-0009',
    transactionType: 'FE',
    accountNumber: '100000003',
    portfolioId: 'PORT0003',
    transactionDate: '2026-01-09',
    fundId: '',
    quantity: 0.0000,
    price: 0.0000,
    amount: 15.5000,
    currency: 'USD',
    status: 'P',
    description: 'Quarterly advisory fee',
  },
  {
    transactionId: '20260110-0010',
    transactionType: 'BU',
    accountNumber: '100000006',
    portfolioId: 'PORT0006',
    transactionDate: '2026-01-10',
    fundId: 'NVDA01',
    quantity: 40.0000,
    price: 135.2500,
    amount: 5410.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260111-0011',
    transactionType: 'SL',
    accountNumber: '100000006',
    portfolioId: 'PORT0006',
    transactionDate: '2026-01-11',
    fundId: 'META01',
    quantity: 60.0000,
    price: 580.0000,
    amount: 34800.0000,
    currency: 'USD',
    status: 'F',
  },
  {
    transactionId: '20260112-0012',
    transactionType: 'TR',
    accountNumber: '100000007',
    portfolioId: 'PORT0007',
    transactionDate: '2026-01-12',
    fundId: 'MSFT02',
    quantity: 100.0000,
    price: 0.0000,
    amount: 0.0000,
    currency: 'USD',
    status: 'R',
    sourceAccount: '100000007',
    destinationAccount: '100000002',
  },
  {
    transactionId: '20260113-0013',
    transactionType: 'BU',
    accountNumber: '100000008',
    portfolioId: 'PORT0008',
    transactionDate: '2026-01-13',
    fundId: 'BOND03',
    quantity: 500.0000,
    price: 99.7500,
    amount: 49875.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260114-0014',
    transactionType: 'FE',
    accountNumber: '100000008',
    portfolioId: 'PORT0008',
    transactionDate: '2026-01-14',
    fundId: '',
    quantity: 0.0000,
    price: 0.0000,
    amount: 50.0000,
    currency: 'USD',
    status: 'R',
    description: 'Wire transfer fee',
  },
  {
    transactionId: '20260115-0015',
    transactionType: 'SL',
    accountNumber: '100000009',
    portfolioId: 'PORT0009',
    transactionDate: '2026-01-15',
    fundId: 'GOOG01',
    quantity: 10.0000,
    price: 178.0000,
    amount: 1780.0000,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260116-0016',
    transactionType: 'BU',
    accountNumber: '100000009',
    portfolioId: 'PORT0009',
    transactionDate: '2026-01-16',
    fundId: 'INTL01',
    quantity: 150.0000,
    price: 22.5000,
    amount: 3375.0000,
    currency: 'USD',
    status: 'D',
  },
  {
    transactionId: '20260117-0017',
    transactionType: 'TR',
    accountNumber: '200000001',
    portfolioId: 'PRTF0010',
    transactionDate: '2026-01-17',
    fundId: 'TSLA01',
    quantity: 25.0000,
    price: 0.0000,
    amount: 0.0000,
    currency: 'USD',
    status: 'F',
    sourceAccount: '200000001',
    destinationAccount: '200000002',
  },
  {
    transactionId: '20260118-0018',
    transactionType: 'FE',
    accountNumber: '200000002',
    portfolioId: 'PRTF0011',
    transactionDate: '2026-01-18',
    fundId: '',
    quantity: 0.0000,
    price: 0.0000,
    amount: 75.0000,
    currency: 'USD',
    status: 'F',
    description: 'Late payment penalty',
  },
  {
    transactionId: '20260119-0019',
    transactionType: 'BU',
    accountNumber: '300000001',
    portfolioId: 'PRTF0012',
    transactionDate: '2026-01-19',
    fundId: 'AMZN01',
    quantity: 80.0000,
    price: 198.5000,
    amount: 15880.0000,
    currency: 'USD',
    status: 'P',
  },
  {
    transactionId: '20260120-0020',
    transactionType: 'SL',
    accountNumber: '300000001',
    portfolioId: 'PRTF0012',
    transactionDate: '2026-01-20',
    fundId: 'NVDA01',
    quantity: 45.0000,
    price: 140.0000,
    amount: 6300.0000,
    currency: 'USD',
    status: 'D',
  },
];

let transactions: Transaction[] = [...seedTransactions];
let sequenceCounter = 21;

export const transactionStore = {
  getAll(): Transaction[] {
    return [...transactions];
  },

  getById(transactionId: string): Transaction | undefined {
    return transactions.find((t) => t.transactionId === transactionId);
  },

  add(transaction: Omit<Transaction, 'transactionId' | 'status'>): Transaction {
    const now = new Date();
    const dateStr = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`;
    const seq = String(sequenceCounter++).padStart(4, '0');
    const newTransaction: Transaction = {
      ...transaction,
      transactionId: `${dateStr}-${seq}`,
      status: 'P',
    };
    transactions = [newTransaction, ...transactions];
    return newTransaction;
  },

  updateStatus(transactionId: string, status: TransactionStatus): boolean {
    const index = transactions.findIndex((t) => t.transactionId === transactionId);
    if (index === -1) return false;
    transactions[index] = { ...transactions[index], status };
    return true;
  },

  filter(params: {
    status?: TransactionStatus;
    transactionType?: TransactionType;
    accountNumber?: string;
    dateFrom?: string;
    dateTo?: string;
  }): Transaction[] {
    return transactions.filter((t) => {
      if (params.status && t.status !== params.status) return false;
      if (params.transactionType && t.transactionType !== params.transactionType) return false;
      if (params.accountNumber && !t.accountNumber.includes(params.accountNumber)) return false;
      if (params.dateFrom && t.transactionDate < params.dateFrom) return false;
      if (params.dateTo && t.transactionDate > params.dateTo) return false;
      return true;
    });
  },

  sort(items: Transaction[], field: keyof Transaction, direction: 'asc' | 'desc'): Transaction[] {
    return [...items].sort((a, b) => {
      const aVal = a[field];
      const bVal = b[field];
      if (aVal === undefined && bVal === undefined) return 0;
      if (aVal === undefined) return direction === 'asc' ? -1 : 1;
      if (bVal === undefined) return direction === 'asc' ? 1 : -1;
      if (aVal < bVal) return direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return direction === 'asc' ? 1 : -1;
      return 0;
    });
  },
};
