import { useState, useEffect, useMemo } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button } from '../components';
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
import type { Transaction, TransactionStatus as TxnStatus, TransactionType } from '../types/transaction';
import {
  STATUS_LABELS,
  STATUS_COLORS,
  TRANSACTION_TYPE_LABELS,
} from '../types/transaction';

type SortField = keyof Transaction;
type SortDirection = 'asc' | 'desc';

const PAGE_SIZE = 10;

const ALL_STATUSES: TxnStatus[] = ['P', 'D', 'F', 'R'];

export default function TransactionStatus() {
  const location = useLocation();

  // Parse highlight param from URL
  const highlightId = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return params.get('highlight') || null;
  }, [location.search]);

  // Filters
  const [statusFilter, setStatusFilter] = useState<TxnStatus | ''>('');
  const [accountSearch, setAccountSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  // Sort
  const [sortField, setSortField] = useState<SortField>('transactionDate');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);

  // Detail expand
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  // Highlight animation
  const [flashId, setFlashId] = useState<string | null>(highlightId);

  useEffect(() => {
    if (highlightId) {
      setFlashId(highlightId);
      const timer = setTimeout(() => setFlashId(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [highlightId]);

  // Get filtered & sorted transactions
  const filteredTransactions = useMemo(() => {
    const criteria: {
      status?: TxnStatus;
      type?: TransactionType;
      accountNumber?: string;
      dateFrom?: string;
      dateTo?: string;
    } = {};
    if (statusFilter) criteria.status = statusFilter;
    if (accountSearch) criteria.accountNumber = accountSearch;
    if (dateFrom) criteria.dateFrom = dateFrom;
    if (dateTo) criteria.dateTo = dateTo;

    const filtered = transactionStore.filter(criteria);
    return transactionStore.sort(filtered, sortField, sortDirection);
  }, [statusFilter, accountSearch, dateFrom, dateTo, sortField, sortDirection]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filteredTransactions.length / PAGE_SIZE));
  const paginatedTransactions = filteredTransactions.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [statusFilter, accountSearch, dateFrom, dateTo]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const sortIndicator = (field: SortField) => {
    if (sortField !== field) return ' \u2195';
    return sortDirection === 'asc' ? ' \u2191' : ' \u2193';
  };

  const toggleExpand = (id: string) => {
    setExpandedRow((prev) => (prev === id ? null : id));
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="xl">
        <div className="space-y-8">
          <div className="flex items-center justify-between">
            <Link to={ROUTES.MAIN_MENU}>
              <Button variant="secondary" size="sm">
                &larr; Back to Main Menu
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
            {/* Filter Bar */}
            <Card hover={false} padding="sm" className="animate-fade-in">
              <div className="flex flex-wrap gap-4 items-end">
                <div className="flex-1 min-w-[150px]">
                  <label htmlFor="statusFilter" className="block text-xs font-medium text-muted-foreground mb-1">
                    Status
                  </label>
                  <select
                    id="statusFilter"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value as TxnStatus | '')}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] outline-none"
                  >
                    <option value="">All Statuses</option>
                    {ALL_STATUSES.map((s) => (
                      <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                    ))}
                  </select>
                </div>
                <div className="flex-1 min-w-[150px]">
                  <label htmlFor="accountSearch" className="block text-xs font-medium text-muted-foreground mb-1">
                    Account Number
                  </label>
                  <Input
                    id="accountSearch"
                    placeholder="Search account..."
                    value={accountSearch}
                    onChange={(e) => setAccountSearch((e.target as HTMLInputElement).value)}
                  />
                </div>
                <div className="flex-1 min-w-[140px]">
                  <label htmlFor="dateFrom" className="block text-xs font-medium text-muted-foreground mb-1">
                    From Date
                  </label>
                  <Input
                    id="dateFrom"
                    type="date"
                    value={dateFrom}
                    onChange={(e) => setDateFrom((e.target as HTMLInputElement).value)}
                  />
                </div>
                <div className="flex-1 min-w-[140px]">
                  <label htmlFor="dateTo" className="block text-xs font-medium text-muted-foreground mb-1">
                    To Date
                  </label>
                  <Input
                    id="dateTo"
                    type="date"
                    value={dateTo}
                    onChange={(e) => setDateTo((e.target as HTMLInputElement).value)}
                  />
                </div>
              </div>
            </Card>

            {/* Transaction Table */}
            <Card hover={false} padding="sm" className="animate-fade-in overflow-hidden">
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
                  {paginatedTransactions.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center text-muted-foreground py-8">
                        No transactions found matching the current filters.
                      </TableCell>
                    </TableRow>
                  ) : (
                    paginatedTransactions.map((txn) => (
                      <TransactionRow
                        key={txn.transactionId}
                        transaction={txn}
                        isHighlighted={flashId === txn.transactionId}
                        isExpanded={expandedRow === txn.transactionId}
                        onToggleExpand={() => toggleExpand(txn.transactionId)}
                      />
                    ))
                  )}
                </TableBody>
              </Table>
            </Card>

            {/* Pagination */}
            <div className="flex items-center justify-between animate-fade-in">
              <p className="text-sm text-muted-foreground">
                Showing {filteredTransactions.length === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1}
                &ndash;{Math.min(currentPage * PAGE_SIZE, filteredTransactions.length)} of {filteredTransactions.length} transactions
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage <= 1}
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground px-2">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage >= totalPages}
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
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

/** Individual transaction row with inline expand detail */
function TransactionRow({
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
  const isTransfer = transaction.transactionType === 'TR';
  const isFee = transaction.transactionType === 'FE';

  return (
    <>
      <TableRow
        className={`cursor-pointer ${isHighlighted ? 'animate-pulse bg-primary/10' : ''}`}
        onClick={onToggleExpand}
      >
        <TableCell className="font-mono text-xs">{transaction.transactionId}</TableCell>
        <TableCell>{transaction.transactionDate}</TableCell>
        <TableCell>{TRANSACTION_TYPE_LABELS[transaction.transactionType]}</TableCell>
        <TableCell className="font-mono text-xs">{transaction.accountNumber}</TableCell>
        <TableCell className="font-mono text-xs">{transaction.fundId}</TableCell>
        <TableCell className="text-right">{transaction.quantity.toFixed(4)}</TableCell>
        <TableCell className="text-right">${transaction.price.toFixed(4)}</TableCell>
        <TableCell className="text-right font-medium">${transaction.amount.toFixed(2)}</TableCell>
        <TableCell>
          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${STATUS_COLORS[transaction.status]}`}>
            {STATUS_LABELS[transaction.status]}
          </span>
        </TableCell>
      </TableRow>
      {isExpanded && (
        <TableRow>
          <TableCell colSpan={9} className="bg-muted/30 p-4">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-x-8 gap-y-2 text-sm">
              <div>
                <span className="text-muted-foreground">Transaction ID:</span>{' '}
                <span className="font-mono">{transaction.transactionId}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Type:</span>{' '}
                {TRANSACTION_TYPE_LABELS[transaction.transactionType]}
              </div>
              <div>
                <span className="text-muted-foreground">Status:</span>{' '}
                {STATUS_LABELS[transaction.status]}
              </div>
              <div>
                <span className="text-muted-foreground">Date:</span>{' '}
                {transaction.transactionDate}
              </div>
              <div>
                <span className="text-muted-foreground">Portfolio ID:</span>{' '}
                <span className="font-mono">{transaction.portfolioId}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Currency:</span>{' '}
                {transaction.currency}
              </div>
              {isTransfer && (
                <>
                  <div>
                    <span className="text-muted-foreground">Source Account:</span>{' '}
                    <span className="font-mono">{transaction.sourceAccount}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Destination Account:</span>{' '}
                    <span className="font-mono">{transaction.destinationAccount}</span>
                  </div>
                </>
              )}
              {!isTransfer && (
                <div>
                  <span className="text-muted-foreground">Account:</span>{' '}
                  <span className="font-mono">{transaction.accountNumber}</span>
                </div>
              )}
              <div>
                <span className="text-muted-foreground">Fund ID:</span>{' '}
                <span className="font-mono">{transaction.fundId}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Quantity:</span>{' '}
                {transaction.quantity.toFixed(4)}
              </div>
              <div>
                <span className="text-muted-foreground">Price:</span>{' '}
                ${transaction.price.toFixed(4)}
              </div>
              <div>
                <span className="text-muted-foreground">Amount:</span>{' '}
                <span className="font-medium">${transaction.amount.toFixed(2)}</span>
              </div>
              {isFee && transaction.description && (
                <div className="col-span-full">
                  <span className="text-muted-foreground">Description:</span>{' '}
                  {transaction.description}
                </div>
              )}
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}
