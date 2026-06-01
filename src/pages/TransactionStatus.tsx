import { useState, useEffect, useCallback } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Button } from '../components';
import { Input } from '../components/ui/input';
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '../components/ui/table';
import { transactionStore } from '../data/mockTransactions';
import type { Transaction, TransactionType, TransactionStatus as TxnStatus } from '../types/transaction';
import {
  TRANSACTION_TYPE_LABELS,
  STATUS_LABELS,
  STATUS_COLORS,
} from '../types/transaction';

type SortField = 'transactionId' | 'transactionDate' | 'transactionType' | 'accountNumber' | 'fundId' | 'quantity' | 'price' | 'amount' | 'status';
type SortDirection = 'asc' | 'desc';

const PAGE_SIZE = 10;

export default function TransactionStatus() {
  const location = useLocation();
  const urlParams = new URLSearchParams(location.search);
  const highlightId = urlParams.get('highlight');

  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [statusFilter, setStatusFilter] = useState<TxnStatus | ''>('');
  const [accountSearch, setAccountSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [sortField, setSortField] = useState<SortField>('transactionDate');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const loadTransactions = useCallback(() => {
    let data = transactionStore.getAll();

    if (statusFilter) {
      data = data.filter((t) => t.status === statusFilter);
    }
    if (accountSearch) {
      data = data.filter(
        (t) =>
          t.accountNumber.includes(accountSearch) ||
          (t.sourceAccount && t.sourceAccount.includes(accountSearch)) ||
          (t.destinationAccount && t.destinationAccount.includes(accountSearch)),
      );
    }
    if (dateFrom) {
      data = data.filter((t) => t.transactionDate >= dateFrom);
    }
    if (dateTo) {
      data = data.filter((t) => t.transactionDate <= dateTo);
    }

    data.sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    setTransactions(data);
  }, [statusFilter, accountSearch, dateFrom, dateTo, sortField, sortDirection]);

  useEffect(() => {
    loadTransactions();
  }, [loadTransactions]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [statusFilter, accountSearch, dateFrom, dateTo]);

  const totalPages = Math.max(1, Math.ceil(transactions.length / PAGE_SIZE));
  const pagedTransactions = transactions.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE,
  );

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const sortIndicator = (field: SortField) => {
    if (sortField !== field) return '';
    return sortDirection === 'asc' ? ' \u2191' : ' \u2193';
  };

  const toggleExpand = (txnId: string) => {
    setExpandedRow((prev) => (prev === txnId ? null : txnId));
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="lg">
        <div className="space-y-8">
          <div className="flex items-center justify-between">
            <Link to={ROUTES.MAIN_MENU}>
              <Button variant="secondary" size="sm">
                ← Back to Main Menu
              </Button>
            </Link>
            <Link to={ROUTES.TRANSACTION_SUBMIT}>
              <Button variant="primary" size="sm">
                Submit New Transaction
              </Button>
            </Link>
          </div>

          <PageHeader
            title="Transaction Status"
            subtitle="Track and monitor submitted transactions"
          />

          <main className="space-y-6 animate-slide-up">
            {/* Filter bar */}
            <div className="flex flex-wrap gap-4 items-end animate-fade-in">
              <div>
                <label htmlFor="statusFilter" className="block text-sm font-medium mb-1">
                  Status
                </label>
                <select
                  id="statusFilter"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as TxnStatus | '')}
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                >
                  <option value="">All Statuses</option>
                  <option value="P">Pending</option>
                  <option value="D">Processed</option>
                  <option value="F">Failed</option>
                  <option value="R">Reversed</option>
                </select>
              </div>

              <div>
                <label htmlFor="dateFrom" className="block text-sm font-medium mb-1">
                  Date From
                </label>
                <Input
                  id="dateFrom"
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                />
              </div>

              <div>
                <label htmlFor="dateTo" className="block text-sm font-medium mb-1">
                  Date To
                </label>
                <Input
                  id="dateTo"
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                />
              </div>

              <div>
                <label htmlFor="accountSearch" className="block text-sm font-medium mb-1">
                  Account Search
                </label>
                <Input
                  id="accountSearch"
                  placeholder="Search account number"
                  value={accountSearch}
                  onChange={(e) => setAccountSearch(e.target.value)}
                />
              </div>
            </div>

            {/* Transaction table */}
            <div className="bg-card border border-border rounded-lg shadow-sm animate-fade-in">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => handleSort('transactionId')}
                    >
                      Transaction ID{sortIndicator('transactionId')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => handleSort('transactionDate')}
                    >
                      Date{sortIndicator('transactionDate')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => handleSort('transactionType')}
                    >
                      Type{sortIndicator('transactionType')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => handleSort('accountNumber')}
                    >
                      Account{sortIndicator('accountNumber')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => handleSort('fundId')}
                    >
                      Fund ID{sortIndicator('fundId')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none text-right"
                      onClick={() => handleSort('quantity')}
                    >
                      Quantity{sortIndicator('quantity')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none text-right"
                      onClick={() => handleSort('price')}
                    >
                      Price{sortIndicator('price')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none text-right"
                      onClick={() => handleSort('amount')}
                    >
                      Amount{sortIndicator('amount')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => handleSort('status')}
                    >
                      Status{sortIndicator('status')}
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {pagedTransactions.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center text-muted-foreground py-8">
                        No transactions found matching the current filters.
                      </TableCell>
                    </TableRow>
                  ) : (
                    pagedTransactions.map((txn) => (
                      <TransactionRowGroup
                        key={txn.transactionId}
                        transaction={txn}
                        isHighlighted={txn.transactionId === highlightId}
                        isExpanded={expandedRow === txn.transactionId}
                        onToggleExpand={() => toggleExpand(txn.transactionId)}
                      />
                    ))
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between animate-fade-in">
              <p className="text-sm text-muted-foreground">
                Showing {transactions.length === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1}–
                {Math.min(currentPage * PAGE_SIZE, transactions.length)} of {transactions.length}{' '}
                transactions
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage <= 1}
                  onClick={() => setCurrentPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <span className="text-sm font-medium px-2">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage >= totalPages}
                  onClick={() => setCurrentPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          </main>
        </div>
      </Container>
    </div>
  );
}

function TransactionRowGroup({
  transaction,
  isHighlighted,
  isExpanded,
  onToggleExpand,
}: {
  transaction: Transaction;
  isHighlighted: boolean;
  isExpanded: boolean;
  onToggleExpand: () => void;
}) {
  const highlightClass = isHighlighted
    ? 'animate-pulse bg-primary/10'
    : '';

  return (
    <>
      <TableRow
        className={`cursor-pointer ${highlightClass}`}
        onClick={onToggleExpand}
      >
        <TableCell className="font-mono text-xs">{transaction.transactionId}</TableCell>
        <TableCell>{transaction.transactionDate}</TableCell>
        <TableCell>
          {TRANSACTION_TYPE_LABELS[transaction.transactionType as TransactionType]}
        </TableCell>
        <TableCell className="font-mono">{transaction.accountNumber}</TableCell>
        <TableCell className="font-mono">{transaction.fundId}</TableCell>
        <TableCell className="text-right">{transaction.quantity.toFixed(4)}</TableCell>
        <TableCell className="text-right">
          ${transaction.price.toFixed(4)}
        </TableCell>
        <TableCell className="text-right font-medium">
          ${transaction.amount.toFixed(2)}
        </TableCell>
        <TableCell>
          <span
            className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${STATUS_COLORS[transaction.status as TxnStatus]}`}
          >
            {STATUS_LABELS[transaction.status as TxnStatus]}
          </span>
        </TableCell>
      </TableRow>

      {isExpanded && (
        <TableRow>
          <TableCell colSpan={9} className="bg-muted/30 p-4">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
              <DetailField label="Transaction ID" value={transaction.transactionId} />
              <DetailField
                label="Type"
                value={`${TRANSACTION_TYPE_LABELS[transaction.transactionType as TransactionType]} (${transaction.transactionType})`}
              />
              <DetailField
                label="Status"
                value={STATUS_LABELS[transaction.status as TxnStatus]}
              />
              <DetailField label="Date" value={transaction.transactionDate} />
              <DetailField label="Account" value={transaction.accountNumber} />
              <DetailField label="Portfolio ID" value={transaction.portfolioId} />
              <DetailField label="Fund ID" value={transaction.fundId} />
              <DetailField label="Quantity" value={transaction.quantity.toFixed(4)} />
              <DetailField label="Price" value={`$${transaction.price.toFixed(4)}`} />
              <DetailField label="Amount" value={`$${transaction.amount.toFixed(2)}`} />
              <DetailField label="Currency" value={transaction.currency} />
              {transaction.sourceAccount && (
                <DetailField label="Source Account" value={transaction.sourceAccount} />
              )}
              {transaction.destinationAccount && (
                <DetailField label="Destination Account" value={transaction.destinationAccount} />
              )}
              {transaction.description && (
                <DetailField label="Description" value={transaction.description} />
              )}
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-muted-foreground">{label}</span>
      <p className="font-medium">{value}</p>
    </div>
  );
}
