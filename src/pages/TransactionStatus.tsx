import { useState, useEffect, useMemo } from 'react';
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
  TransactionStatus as TxnStatus,
  STATUS_LABELS,
  STATUS_COLORS,
  TRANSACTION_TYPE_LABELS,
} from '../types/transaction';

type SortField = keyof Transaction;
type SortDir = 'asc' | 'desc';

const PAGE_SIZE = 10;
const ALL_STATUSES: TxnStatus[] = ['P', 'D', 'F', 'R'];

export default function TransactionStatus() {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const highlightId = params.get('highlight') ?? '';

  const [statusFilter, setStatusFilter] = useState<TxnStatus | ''>('');
  const [accountSearch, setAccountSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [sortField, setSortField] = useState<SortField>('transactionDate');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [page, setPage] = useState(0);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [highlightActive, setHighlightActive] = useState(!!highlightId);

  useEffect(() => {
    if (highlightId) {
      const timer = setTimeout(() => setHighlightActive(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [highlightId]);

  const [allTransactions, setAllTransactions] = useState(() => transactionStore.getAll());

  useEffect(() => {
    setAllTransactions(transactionStore.getAll());
  }, [location.search]);

  const filtered = useMemo(() => {
    let result = allTransactions;
    if (statusFilter) {
      result = result.filter((t) => t.status === statusFilter);
    }
    if (accountSearch.trim()) {
      result = result.filter((t) =>
        t.accountNumber.includes(accountSearch.trim())
      );
    }
    if (dateFrom) {
      result = result.filter((t) => t.transactionDate >= dateFrom);
    }
    if (dateTo) {
      result = result.filter((t) => t.transactionDate <= dateTo);
    }
    return result;
  }, [allTransactions, statusFilter, accountSearch, dateFrom, dateTo]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      if (aVal === undefined || bVal === undefined) return 0;
      if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filtered, sortField, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const paginated = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  function handleSort(field: SortField) {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('asc');
    }
    setPage(0);
  }

  function sortIndicator(field: SortField) {
    if (sortField !== field) return '';
    return sortDir === 'asc' ? ' ↑' : ' ↓';
  }

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
            subtitle="Track and review submitted transactions"
          />

          <main className="space-y-6 animate-slide-up">
            {/* Filter Bar */}
            <div className="flex flex-wrap gap-4 items-end animate-fade-in">
              <div>
                <label
                  htmlFor="statusFilter"
                  className="block text-sm font-medium mb-1"
                >
                  Status
                </label>
                <select
                  id="statusFilter"
                  value={statusFilter}
                  onChange={(e) => {
                    setStatusFilter(e.target.value as TxnStatus | '');
                    setPage(0);
                  }}
                  className="flex h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] outline-none"
                >
                  <option value="">All Statuses</option>
                  {ALL_STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {STATUS_LABELS[s]}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label
                  htmlFor="accountSearch"
                  className="block text-sm font-medium mb-1"
                >
                  Account
                </label>
                <Input
                  id="accountSearch"
                  placeholder="Search account..."
                  value={accountSearch}
                  onChange={(e) => {
                    setAccountSearch(e.target.value);
                    setPage(0);
                  }}
                  className="w-40"
                />
              </div>

              <div>
                <label
                  htmlFor="dateFrom"
                  className="block text-sm font-medium mb-1"
                >
                  From Date
                </label>
                <Input
                  id="dateFrom"
                  type="date"
                  value={dateFrom}
                  onChange={(e) => {
                    setDateFrom(e.target.value);
                    setPage(0);
                  }}
                />
              </div>

              <div>
                <label
                  htmlFor="dateTo"
                  className="block text-sm font-medium mb-1"
                >
                  To Date
                </label>
                <Input
                  id="dateTo"
                  type="date"
                  value={dateTo}
                  onChange={(e) => {
                    setDateTo(e.target.value);
                    setPage(0);
                  }}
                />
              </div>
            </div>

            {/* Table */}
            <div className="border rounded-lg animate-fade-in">
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
                  {paginated.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                        No transactions match the current filters.
                      </TableCell>
                    </TableRow>
                  ) : (
                    paginated.map((txn) => (
                      <TransactionRow
                        key={txn.transactionId}
                        transaction={txn}
                        isHighlighted={
                          highlightActive && txn.transactionId === highlightId
                        }
                        isExpanded={expandedId === txn.transactionId}
                        onToggleExpand={() =>
                          setExpandedId((prev) =>
                            prev === txn.transactionId
                              ? null
                              : txn.transactionId
                          )
                        }
                      />
                    ))
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between animate-fade-in">
              <p className="text-sm text-muted-foreground">
                Showing {sorted.length === 0 ? 0 : page * PAGE_SIZE + 1}–
                {Math.min((page + 1) * PAGE_SIZE, sorted.length)} of{' '}
                {sorted.length} transactions
              </p>
              <div className="flex gap-2 items-center">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 0}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <span className="text-sm">
                  Page {page + 1} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage((p) => p + 1)}
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
  const txn = transaction;
  return (
    <>
      <TableRow
        className={`cursor-pointer ${
          isHighlighted
            ? 'animate-pulse bg-primary/10'
            : ''
        }`}
        onClick={onToggleExpand}
      >
        <TableCell className="font-mono text-xs">{txn.transactionId}</TableCell>
        <TableCell>{txn.transactionDate}</TableCell>
        <TableCell>{TRANSACTION_TYPE_LABELS[txn.transactionType]}</TableCell>
        <TableCell className="font-mono">{txn.accountNumber}</TableCell>
        <TableCell className="font-mono">{txn.fundId || '—'}</TableCell>
        <TableCell className="text-right">
          {txn.quantity ? txn.quantity.toFixed(4) : '—'}
        </TableCell>
        <TableCell className="text-right">
          {txn.price ? `$${txn.price.toFixed(2)}` : '—'}
        </TableCell>
        <TableCell className="text-right font-medium">
          ${txn.amount.toFixed(2)}
        </TableCell>
        <TableCell>
          <span
            className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
              STATUS_COLORS[txn.status]
            }`}
          >
            {STATUS_LABELS[txn.status]}
          </span>
        </TableCell>
      </TableRow>
      {isExpanded && (
        <TableRow>
          <TableCell colSpan={9} className="bg-muted/30 p-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <Detail label="Transaction ID" value={txn.transactionId} />
              <Detail
                label="Type"
                value={`${TRANSACTION_TYPE_LABELS[txn.transactionType]} (${txn.transactionType})`}
              />
              <Detail label="Date" value={txn.transactionDate} />
              <Detail label="Status" value={STATUS_LABELS[txn.status]} />
              <Detail label="Account" value={txn.accountNumber} />
              <Detail label="Portfolio ID" value={txn.portfolioId} />
              <Detail label="Fund ID" value={txn.fundId || '—'} />
              <Detail label="Currency" value={txn.currency} />
              <Detail
                label="Quantity"
                value={txn.quantity ? txn.quantity.toFixed(4) : '—'}
              />
              <Detail
                label="Price"
                value={txn.price ? `$${txn.price.toFixed(2)}` : '—'}
              />
              <Detail label="Amount" value={`$${txn.amount.toFixed(2)}`} />
              {txn.sourceAccount && (
                <Detail label="Source Account" value={txn.sourceAccount} />
              )}
              {txn.destinationAccount && (
                <Detail
                  label="Destination Account"
                  value={txn.destinationAccount}
                />
              )}
              {txn.description && (
                <Detail label="Description" value={txn.description} />
              )}
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-muted-foreground text-xs block">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
