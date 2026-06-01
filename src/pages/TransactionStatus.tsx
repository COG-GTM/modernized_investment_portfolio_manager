import React, { useState, useEffect, useMemo } from 'react';
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
  TransactionStatus as TxStatus,
  STATUS_LABELS,
  STATUS_COLORS,
  TRANSACTION_TYPE_LABELS,
} from '../types/transaction';

type SortField = keyof Transaction;
type SortDir = 'asc' | 'desc';

const PAGE_SIZE = 10;

const ALL_STATUSES: TxStatus[] = ['P', 'D', 'F', 'R'];

export default function TransactionStatus() {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const highlightId = params.get('highlight');

  const [allTransactions, setAllTransactions] = useState<Transaction[]>([]);
  const [statusFilter, setStatusFilter] = useState<TxStatus | ''>('');
  const [accountSearch, setAccountSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [sortField, setSortField] = useState<SortField>('transactionDate');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [page, setPage] = useState(0);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  useEffect(() => {
    setAllTransactions(transactionStore.getAll());
  }, []);

  const filtered = useMemo(() => {
    let result = allTransactions;
    if (statusFilter) {
      result = result.filter((t) => t.status === statusFilter);
    }
    if (accountSearch) {
      result = result.filter((t) => t.accountNumber.includes(accountSearch));
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
      if (aVal === undefined && bVal === undefined) return 0;
      if (aVal === undefined) return 1;
      if (bVal === undefined) return -1;
      if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filtered, sortField, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const paginated = sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDir('asc');
    }
    setPage(0);
  };

  const sortIndicator = (field: SortField) => {
    if (sortField !== field) return '';
    return sortDir === 'asc' ? ' ↑' : ' ↓';
  };

  const toggleExpand = (id: string) => {
    setExpandedRow(expandedRow === id ? null : id);
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
            subtitle="Track and monitor your transaction submissions"
          />

          <main className="space-y-6 animate-slide-up">
            {/* Filter Bar */}
            <div className="flex flex-wrap gap-4 items-end">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Status</label>
                <select
                  value={statusFilter}
                  onChange={(e) => {
                    setStatusFilter(e.target.value as TxStatus | '');
                    setPage(0);
                  }}
                  className="flex h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
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
                <label className="block text-sm font-medium text-foreground mb-1">Account</label>
                <Input
                  value={accountSearch}
                  onChange={(e) => {
                    setAccountSearch(e.target.value);
                    setPage(0);
                  }}
                  placeholder="Search account..."
                  className="w-40"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Date From</label>
                <Input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => {
                    setDateFrom(e.target.value);
                    setPage(0);
                  }}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Date To</label>
                <Input
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
            <div className="bg-card border border-border rounded-lg shadow-sm overflow-hidden">
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
                  {paginated.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                        No transactions found matching your filters.
                      </TableCell>
                    </TableRow>
                  ) : (
                    paginated.map((tx) => {
                      const isHighlighted = tx.transactionId === highlightId;
                      const isExpanded = expandedRow === tx.transactionId;
                      return (
                        <React.Fragment key={tx.transactionId}>
                          <TableRow
                            className={`cursor-pointer ${
                              isHighlighted ? 'animate-pulse bg-primary/10' : ''
                            }`}
                            onClick={() => toggleExpand(tx.transactionId)}
                          >
                            <TableCell className="font-mono text-xs">
                              {tx.transactionId}
                            </TableCell>
                            <TableCell>{tx.transactionDate}</TableCell>
                            <TableCell>{TRANSACTION_TYPE_LABELS[tx.transactionType]}</TableCell>
                            <TableCell className="font-mono">{tx.accountNumber}</TableCell>
                            <TableCell className="font-mono">{tx.fundId}</TableCell>
                            <TableCell className="text-right">
                              {tx.quantity.toFixed(4)}
                            </TableCell>
                            <TableCell className="text-right">
                              ${tx.price.toFixed(4)}
                            </TableCell>
                            <TableCell className="text-right font-medium">
                              ${tx.amount.toFixed(2)}
                            </TableCell>
                            <TableCell>
                              <span
                                className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${STATUS_COLORS[tx.status]}`}
                              >
                                {STATUS_LABELS[tx.status]}
                              </span>
                            </TableCell>
                          </TableRow>
                          {isExpanded && (
                            <TableRow>
                              <TableCell colSpan={9} className="bg-muted/30 p-4">
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                                  <DetailItem label="Transaction ID" value={tx.transactionId} />
                                  <DetailItem label="Type" value={TRANSACTION_TYPE_LABELS[tx.transactionType]} />
                                  <DetailItem label="Status" value={STATUS_LABELS[tx.status]} />
                                  <DetailItem label="Date" value={tx.transactionDate} />
                                  <DetailItem label="Account" value={tx.accountNumber} />
                                  <DetailItem label="Portfolio ID" value={tx.portfolioId} />
                                  <DetailItem label="Fund ID" value={tx.fundId} />
                                  <DetailItem label="Quantity" value={tx.quantity.toFixed(4)} />
                                  <DetailItem label="Price" value={`$${tx.price.toFixed(4)}`} />
                                  <DetailItem label="Amount" value={`$${tx.amount.toFixed(2)}`} />
                                  <DetailItem label="Currency" value={tx.currency} />
                                  {tx.sourceAccount && (
                                    <DetailItem label="Source Account" value={tx.sourceAccount} />
                                  )}
                                  {tx.destinationAccount && (
                                    <DetailItem label="Destination Account" value={tx.destinationAccount} />
                                  )}
                                  {tx.description && (
                                    <DetailItem label="Description" value={tx.description} />
                                  )}
                                </div>
                              </TableCell>
                            </TableRow>
                          )}
                        </React.Fragment>
                      );
                    })
                  )}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Showing {sorted.length === 0 ? 0 : page * PAGE_SIZE + 1}–
                {Math.min((page + 1) * PAGE_SIZE, sorted.length)} of {sorted.length} transactions
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 0}
                  onClick={() => setPage(page - 1)}
                >
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {page + 1} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage(page + 1)}
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

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-muted-foreground text-xs">{label}</span>
      <p className="font-medium">{value}</p>
    </div>
  );
}
