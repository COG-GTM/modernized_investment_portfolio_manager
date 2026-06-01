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
import {
  Transaction,
  TransactionStatus as TxnStatusType,
  STATUS_LABELS,
  STATUS_COLORS,
  TRANSACTION_TYPE_LABELS,
} from '../types/transaction';

type SortField = keyof Transaction;
type SortDir = 'asc' | 'desc';

const PAGE_SIZE = 10;

const statusOptions: { value: '' | TxnStatusType; label: string }[] = [
  { value: '', label: 'All Statuses' },
  { value: 'P', label: 'Pending' },
  { value: 'D', label: 'Processed' },
  { value: 'F', label: 'Failed' },
  { value: 'R', label: 'Reversed' },
];

export default function TransactionStatus() {
  const location = useLocation();
  const urlParams = new URLSearchParams(location.search);
  const highlightId = urlParams.get('highlight') || '';

  const [statusFilter, setStatusFilter] = useState<'' | TxnStatusType>('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [accountSearch, setAccountSearch] = useState('');
  const [sortField, setSortField] = useState<SortField>('transactionDate');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [page, setPage] = useState(1);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [highlightActive, setHighlightActive] = useState(!!highlightId);

  useEffect(() => {
    if (highlightId) {
      const timer = setTimeout(() => setHighlightActive(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [highlightId]);

  const getFilteredSorted = useCallback(() => {
    const filtered = transactionStore.filter({
      status: statusFilter || undefined,
      accountNumber: accountSearch || undefined,
      dateFrom: dateFrom || undefined,
      dateTo: dateTo || undefined,
    });
    return transactionStore.sort(filtered, sortField, sortDir);
  }, [statusFilter, accountSearch, dateFrom, dateTo, sortField, sortDir]);

  const allItems = getFilteredSorted();
  const totalPages = Math.max(1, Math.ceil(allItems.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const pageItems = allItems.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('asc');
    }
    setPage(1);
  };

  const sortIndicator = (field: SortField) => {
    if (sortField !== field) return ' ↕';
    return sortDir === 'asc' ? ' ↑' : ' ↓';
  };

  const toggleExpand = (id: string) => {
    setExpandedRow((prev) => (prev === id ? null : id));
  };

  const handleFilterChange = () => {
    setPage(1);
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="xl">
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
                <label className="block text-sm font-medium mb-1">Status</label>
                <select
                  value={statusFilter}
                  onChange={(e) => {
                    setStatusFilter(e.target.value as '' | TxnStatusType);
                    handleFilterChange();
                  }}
                  className="flex h-9 w-full min-w-[160px] rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-colors focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] outline-none"
                >
                  {statusOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Date From</label>
                <Input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => {
                    setDateFrom(e.target.value);
                    handleFilterChange();
                  }}
                  className="min-w-[150px]"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Date To</label>
                <Input
                  type="date"
                  value={dateTo}
                  onChange={(e) => {
                    setDateTo(e.target.value);
                    handleFilterChange();
                  }}
                  className="min-w-[150px]"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Account Search</label>
                <Input
                  type="text"
                  placeholder="Account number..."
                  value={accountSearch}
                  onChange={(e) => {
                    setAccountSearch(e.target.value);
                    handleFilterChange();
                  }}
                  className="min-w-[180px]"
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
                      className="cursor-pointer select-none"
                      onClick={() => handleSort('quantity')}
                    >
                      Quantity{sortIndicator('quantity')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => handleSort('price')}
                    >
                      Price{sortIndicator('price')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
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
                  {pageItems.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                        No transactions found matching your filters.
                      </TableCell>
                    </TableRow>
                  ) : (
                    pageItems.map((txn) => (
                      <TransactionRowGroup
                        key={txn.transactionId}
                        txn={txn}
                        isExpanded={expandedRow === txn.transactionId}
                        isHighlighted={highlightActive && txn.transactionId === highlightId}
                        onToggle={() => toggleExpand(txn.transactionId)}
                      />
                    ))
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between animate-fade-in">
              <p className="text-sm text-muted-foreground">
                Showing {allItems.length === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1}–
                {Math.min(currentPage * PAGE_SIZE, allItems.length)} of {allItems.length} transactions
              </p>
              <div className="flex gap-2 items-center">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <span className="text-sm px-2">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={currentPage >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
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
  txn,
  isExpanded,
  isHighlighted,
  onToggle,
}: {
  txn: Transaction;
  isExpanded: boolean;
  isHighlighted: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      <TableRow
        className={`cursor-pointer ${isHighlighted ? 'animate-pulse bg-primary/10' : ''}`}
        onClick={onToggle}
      >
        <TableCell className="font-mono text-xs">{txn.transactionId}</TableCell>
        <TableCell>{txn.transactionDate}</TableCell>
        <TableCell>{TRANSACTION_TYPE_LABELS[txn.transactionType]}</TableCell>
        <TableCell className="font-mono">{txn.accountNumber}</TableCell>
        <TableCell className="font-mono">{txn.fundId || '—'}</TableCell>
        <TableCell>{txn.quantity > 0 ? txn.quantity.toFixed(4) : '—'}</TableCell>
        <TableCell>{txn.price > 0 ? `$${txn.price.toFixed(4)}` : '—'}</TableCell>
        <TableCell>${txn.amount.toFixed(2)}</TableCell>
        <TableCell>
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${STATUS_COLORS[txn.status]}`}
          >
            {STATUS_LABELS[txn.status]}
          </span>
        </TableCell>
      </TableRow>
      {isExpanded && (
        <TableRow>
          <TableCell colSpan={9} className="bg-muted/30 p-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="font-medium text-muted-foreground">Transaction ID</span>
                <p className="font-mono">{txn.transactionId}</p>
              </div>
              <div>
                <span className="font-medium text-muted-foreground">Type</span>
                <p>{TRANSACTION_TYPE_LABELS[txn.transactionType]} ({txn.transactionType})</p>
              </div>
              <div>
                <span className="font-medium text-muted-foreground">Date</span>
                <p>{txn.transactionDate}</p>
              </div>
              <div>
                <span className="font-medium text-muted-foreground">Status</span>
                <p>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${STATUS_COLORS[txn.status]}`}
                  >
                    {STATUS_LABELS[txn.status]}
                  </span>
                </p>
              </div>
              <div>
                <span className="font-medium text-muted-foreground">Account</span>
                <p className="font-mono">{txn.accountNumber}</p>
              </div>
              <div>
                <span className="font-medium text-muted-foreground">Portfolio ID</span>
                <p className="font-mono">{txn.portfolioId}</p>
              </div>
              <div>
                <span className="font-medium text-muted-foreground">Fund ID</span>
                <p className="font-mono">{txn.fundId || '—'}</p>
              </div>
              <div>
                <span className="font-medium text-muted-foreground">Currency</span>
                <p>{txn.currency}</p>
              </div>
              <div>
                <span className="font-medium text-muted-foreground">Quantity</span>
                <p>{txn.quantity.toFixed(4)}</p>
              </div>
              <div>
                <span className="font-medium text-muted-foreground">Price</span>
                <p>${txn.price.toFixed(4)}</p>
              </div>
              <div>
                <span className="font-medium text-muted-foreground">Amount</span>
                <p className="font-semibold">${txn.amount.toFixed(2)}</p>
              </div>
              {txn.sourceAccount && (
                <div>
                  <span className="font-medium text-muted-foreground">Source Account</span>
                  <p className="font-mono">{txn.sourceAccount}</p>
                </div>
              )}
              {txn.destinationAccount && (
                <div>
                  <span className="font-medium text-muted-foreground">Destination Account</span>
                  <p className="font-mono">{txn.destinationAccount}</p>
                </div>
              )}
              {txn.description && (
                <div className="col-span-2">
                  <span className="font-medium text-muted-foreground">Description</span>
                  <p>{txn.description}</p>
                </div>
              )}
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}
