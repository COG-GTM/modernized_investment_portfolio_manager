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
  STATUS_LABELS,
  STATUS_COLORS,
  TRANSACTION_TYPE_LABELS,
  type Transaction,
  type TransactionStatus as TxnStatus,
} from '../types/transaction';

const PAGE_SIZE = 10;

type SortField = keyof Transaction;
type SortDir = 'asc' | 'desc';

export default function TransactionStatus() {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const highlightId = params.get('highlight');

  const [statusFilter, setStatusFilter] = useState<TxnStatus | ''>('');
  const [accountSearch, setAccountSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [sortField, setSortField] = useState<SortField>('transactionDate');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [page, setPage] = useState(1);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [highlightActive, setHighlightActive] = useState(!!highlightId);

  // Fade out highlight after 3 seconds
  useEffect(() => {
    if (highlightId) {
      const timer = setTimeout(() => setHighlightActive(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [highlightId]);

  const allTransactions = transactionStore.getAll();

  const filtered = useMemo(() => {
    let list = transactionStore.filter({
      status: statusFilter || undefined,
      accountNumber: accountSearch || undefined,
      dateFrom: dateFrom || undefined,
      dateTo: dateTo || undefined,
    });
    list = transactionStore.sort(list, sortField, sortDir);
    return list;
  }, [allTransactions, statusFilter, accountSearch, dateFrom, dateTo, sortField, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // Reset to page 1 when filters change
  useEffect(() => {
    setPage(1);
  }, [statusFilter, accountSearch, dateFrom, dateTo]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('asc');
    }
  };

  const sortIndicator = (field: SortField) => {
    if (sortField !== field) return ' ↕';
    return sortDir === 'asc' ? ' ↑' : ' ↓';
  };

  const formatCurrency = (value: number, currency: string) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      minimumFractionDigits: 2,
    }).format(value);

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
            subtitle="Track and monitor submitted transactions — maps to legacy batch pipeline: TRNVAL00 → POSUPD00 → HISTLD00"
          />

          <main className="space-y-6 animate-slide-up">
            {/* Filter Bar */}
            <div className="flex flex-wrap gap-4 items-end animate-fade-in">
              <div>
                <label className="block text-sm font-medium mb-1">Status</label>
                <select
                  value={statusFilter}
                  onChange={(e) =>
                    setStatusFilter(e.target.value as TxnStatus | '')
                  }
                  className="h-9 rounded-md border border-input bg-transparent px-3 text-sm focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] outline-none"
                >
                  <option value="">All</option>
                  <option value="P">Pending</option>
                  <option value="D">Processed</option>
                  <option value="F">Failed</option>
                  <option value="R">Reversed</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">
                  Account
                </label>
                <Input
                  placeholder="Search account..."
                  value={accountSearch}
                  onChange={(e) =>
                    setAccountSearch(
                      (e as React.ChangeEvent<HTMLInputElement>).target.value
                    )
                  }
                  className="w-40"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">From</label>
                <Input
                  type="date"
                  value={dateFrom}
                  onChange={(e) =>
                    setDateFrom(
                      (e as React.ChangeEvent<HTMLInputElement>).target.value
                    )
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">To</label>
                <Input
                  type="date"
                  value={dateTo}
                  onChange={(e) =>
                    setDateTo(
                      (e as React.ChangeEvent<HTMLInputElement>).target.value
                    )
                  }
                />
              </div>
            </div>

            {/* Transaction Table */}
            <div className="border rounded-lg overflow-hidden animate-fade-in">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => toggleSort('transactionId')}
                    >
                      Transaction ID{sortIndicator('transactionId')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => toggleSort('transactionDate')}
                    >
                      Date{sortIndicator('transactionDate')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => toggleSort('transactionType')}
                    >
                      Type{sortIndicator('transactionType')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => toggleSort('accountNumber')}
                    >
                      Account{sortIndicator('accountNumber')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => toggleSort('fundId')}
                    >
                      Fund ID{sortIndicator('fundId')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => toggleSort('quantity')}
                    >
                      Quantity{sortIndicator('quantity')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => toggleSort('price')}
                    >
                      Price{sortIndicator('price')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => toggleSort('amount')}
                    >
                      Amount{sortIndicator('amount')}
                    </TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => toggleSort('status')}
                    >
                      Status{sortIndicator('status')}
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paged.length === 0 ? (
                    <TableRow>
                      <TableCell
                        colSpan={9}
                        className="text-center py-8 text-muted-foreground"
                      >
                        No transactions found matching your filters.
                      </TableCell>
                    </TableRow>
                  ) : (
                    paged.map((txn) => {
                      const isHighlighted =
                        highlightActive &&
                        txn.transactionId === highlightId;
                      const isExpanded =
                        expandedId === txn.transactionId;
                      return (
                        <DetailRow
                          key={txn.transactionId}
                          txn={txn}
                          isHighlighted={isHighlighted}
                          isExpanded={isExpanded}
                          onToggle={() =>
                            setExpandedId(
                              isExpanded ? null : txn.transactionId
                            )
                          }
                          formatCurrency={formatCurrency}
                        />
                      );
                    })
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between text-sm animate-fade-in">
              <span className="text-muted-foreground">
                Showing {filtered.length === 0 ? 0 : (page - 1) * PAGE_SIZE + 1}–
                {Math.min(page * PAGE_SIZE, filtered.length)} of{' '}
                {filtered.length} transactions
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <span className="flex items-center px-2">
                  Page {page} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
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

function DetailRow({
  txn,
  isHighlighted,
  isExpanded,
  onToggle,
  formatCurrency,
}: {
  txn: Transaction;
  isHighlighted: boolean;
  isExpanded: boolean;
  onToggle: () => void;
  formatCurrency: (value: number, currency: string) => string;
}) {
  return (
    <>
      <TableRow
        className={`cursor-pointer ${isHighlighted ? 'animate-pulse bg-primary/10' : ''}`}
        onClick={onToggle}
      >
        <TableCell className="font-mono text-xs">
          {txn.transactionId}
        </TableCell>
        <TableCell>{txn.transactionDate}</TableCell>
        <TableCell>
          {TRANSACTION_TYPE_LABELS[txn.transactionType]}
        </TableCell>
        <TableCell className="font-mono">{txn.accountNumber}</TableCell>
        <TableCell className="font-mono">{txn.fundId}</TableCell>
        <TableCell className="text-right">
          {txn.quantity.toFixed(4)}
        </TableCell>
        <TableCell className="text-right">
          {formatCurrency(txn.price, txn.currency)}
        </TableCell>
        <TableCell className="text-right font-medium">
          {formatCurrency(txn.amount, txn.currency)}
        </TableCell>
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
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
              <Detail label="Transaction ID" value={txn.transactionId} />
              <Detail
                label="Type"
                value={`${TRANSACTION_TYPE_LABELS[txn.transactionType]} (${txn.transactionType})`}
              />
              <Detail
                label="Status"
                value={STATUS_LABELS[txn.status]}
              />
              <Detail label="Date" value={txn.transactionDate} />
              <Detail label="Account" value={txn.accountNumber} />
              <Detail label="Portfolio ID" value={txn.portfolioId} />
              <Detail label="Fund ID" value={txn.fundId} />
              <Detail
                label="Quantity"
                value={txn.quantity.toFixed(4)}
              />
              <Detail
                label="Price"
                value={formatCurrency(txn.price, txn.currency)}
              />
              <Detail
                label="Amount"
                value={formatCurrency(txn.amount, txn.currency)}
              />
              <Detail label="Currency" value={txn.currency} />
              {txn.sourceAccount && (
                <Detail
                  label="Source Account"
                  value={txn.sourceAccount}
                />
              )}
              {txn.destinationAccount && (
                <Detail
                  label="Destination Account"
                  value={txn.destinationAccount}
                />
              )}
              {txn.description && (
                <Detail
                  label="Description"
                  value={txn.description}
                />
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
      <span className="text-muted-foreground text-xs">{label}</span>
      <p className="font-medium">{value}</p>
    </div>
  );
}
