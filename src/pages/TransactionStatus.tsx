import { useState, useEffect } from 'react';
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
import type { Transaction, TransactionStatus as TxnStatus } from '../types/transaction';
import {
  STATUS_LABELS,
  STATUS_COLORS,
  TRANSACTION_TYPE_LABELS,
} from '../types/transaction';
import { transactionStore } from '../data/mockTransactions';

type SortField = keyof Transaction;
type SortDir = 'asc' | 'desc';

const PAGE_SIZE = 10;

const statusOptions: Array<{ value: '' | TxnStatus; label: string }> = [
  { value: '', label: 'All Statuses' },
  { value: 'P', label: 'Pending' },
  { value: 'D', label: 'Processed' },
  { value: 'F', label: 'Failed' },
  { value: 'R', label: 'Reversed' },
];

export default function TransactionStatusPage() {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const highlightId = params.get('highlight') ?? '';

  const [filterStatus, setFilterStatus] = useState<'' | TxnStatus>('');
  const [filterAccount, setFilterAccount] = useState('');
  const [filterDateFrom, setFilterDateFrom] = useState('');
  const [filterDateTo, setFilterDateTo] = useState('');
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

  const filtered = transactionStore.filter({
    status: filterStatus || undefined,
    accountNumber: filterAccount || undefined,
    dateFrom: filterDateFrom || undefined,
    dateTo: filterDateTo || undefined,
  });

  const sorted = transactionStore.sort(filtered, sortField, sortDir);
  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const pageData = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('asc');
    }
    setPage(0);
  };

  const sortIndicator = (field: SortField) => {
    if (sortField !== field) return ' \u2195';
    return sortDir === 'asc' ? ' \u2191' : ' \u2193';
  };

  const handleFilterChange = () => {
    setPage(0);
  };

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="lg">
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
            subtitle="Track and review submitted transactions"
          />

          <main className="space-y-6 animate-slide-up">
            {/* Filter Bar */}
            <Card hover={false} className="animate-fade-in">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Status</label>
                  <select
                    value={filterStatus}
                    onChange={(e) => {
                      setFilterStatus(e.target.value as '' | TxnStatus);
                      handleFilterChange();
                    }}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] outline-none"
                  >
                    {statusOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Account Number</label>
                  <Input
                    value={filterAccount}
                    onChange={(e) => {
                      setFilterAccount(e.target.value);
                      handleFilterChange();
                    }}
                    placeholder="Search account..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Date From</label>
                  <Input
                    type="date"
                    value={filterDateFrom}
                    onChange={(e) => {
                      setFilterDateFrom(e.target.value);
                      handleFilterChange();
                    }}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Date To</label>
                  <Input
                    type="date"
                    value={filterDateTo}
                    onChange={(e) => {
                      setFilterDateTo(e.target.value);
                      handleFilterChange();
                    }}
                  />
                </div>
              </div>
            </Card>

            {/* Transaction Table */}
            <div className="animate-fade-in" style={{ animationDelay: '100ms' }}>
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
                  {pageData.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                        No transactions found matching the current filters.
                      </TableCell>
                    </TableRow>
                  ) : (
                    pageData.map((txn) => (
                      <TransactionRow
                        key={txn.transactionId}
                        transaction={txn}
                        isHighlighted={highlightActive && txn.transactionId === highlightId}
                        isExpanded={expandedId === txn.transactionId}
                        onToggle={() => toggleExpand(txn.transactionId)}
                      />
                    ))
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between animate-fade-in" style={{ animationDelay: '200ms' }}>
              <p className="text-sm text-muted-foreground">
                Showing {sorted.length === 0 ? 0 : page * PAGE_SIZE + 1}–
                {Math.min((page + 1) * PAGE_SIZE, sorted.length)} of {sorted.length} transactions
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 0}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <span className="flex items-center text-sm px-2">
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

/* ---- Inline sub-component for each row + expandable detail ---- */

interface TransactionRowProps {
  transaction: Transaction;
  isHighlighted: boolean;
  isExpanded: boolean;
  onToggle: () => void;
}

function TransactionRow({ transaction: txn, isHighlighted, isExpanded, onToggle }: TransactionRowProps) {
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
        <TableCell className="font-mono">{txn.fundId}</TableCell>
        <TableCell className="text-right">{txn.quantity.toFixed(4)}</TableCell>
        <TableCell className="text-right">${txn.price.toFixed(4)}</TableCell>
        <TableCell className="text-right font-medium">${txn.amount.toFixed(2)}</TableCell>
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
          <TableCell colSpan={9} className="bg-muted/30">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 py-3 px-2 text-sm">
              <DetailItem label="Transaction ID" value={txn.transactionId} />
              <DetailItem label="Type" value={`${TRANSACTION_TYPE_LABELS[txn.transactionType]} (${txn.transactionType})`} />
              <DetailItem label="Date" value={txn.transactionDate} />
              <DetailItem label="Status" value={STATUS_LABELS[txn.status]} />
              <DetailItem label="Account" value={txn.accountNumber} />
              <DetailItem label="Portfolio ID" value={txn.portfolioId} />
              <DetailItem label="Fund ID" value={txn.fundId} />
              <DetailItem label="Currency" value={txn.currency} />
              <DetailItem label="Quantity" value={txn.quantity.toFixed(4)} />
              <DetailItem label="Price" value={`$${txn.price.toFixed(4)}`} />
              <DetailItem label="Amount" value={`$${txn.amount.toFixed(2)}`} />
              {txn.sourceAccount && (
                <DetailItem label="Source Account" value={txn.sourceAccount} />
              )}
              {txn.destinationAccount && (
                <DetailItem label="Destination Account" value={txn.destinationAccount} />
              )}
              {txn.description && (
                <DetailItem label="Description" value={txn.description} />
              )}
            </div>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-muted-foreground text-xs">{label}</span>
      <p className="font-medium">{value}</p>
    </div>
  );
}
