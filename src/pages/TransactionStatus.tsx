import React, { useState, useMemo, useEffect } from 'react';
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
import {
  Transaction,
  TransactionStatus as TxStatus,
  TransactionType,
  STATUS_LABELS,
  STATUS_COLORS,
  TRANSACTION_TYPE_LABELS,
} from '../types/transaction';
import { transactionStore } from '../data/mockTransactions';

type SortField = keyof Transaction;
type SortDir = 'asc' | 'desc';

const PAGE_SIZE = 10;

export default function TransactionStatus() {
  const location = useLocation();
  const urlParams = new URLSearchParams(location.search);
  const highlightId = urlParams.get('highlight') || '';

  const [allTransactions, setAllTransactions] = useState<Transaction[]>([]);
  const [statusFilter, setStatusFilter] = useState<TxStatus | ''>('');
  const [typeFilter, setTypeFilter] = useState<TransactionType | ''>('');
  const [accountSearch, setAccountSearch] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [sortField, setSortField] = useState<SortField>('transactionDate');
  const [sortDir, setSortDir] = useState<SortDir>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [highlightActive, setHighlightActive] = useState(!!highlightId);

  // Load transactions
  useEffect(() => {
    setAllTransactions(transactionStore.getAll());
  }, []);

  // Clear highlight animation after a few seconds
  useEffect(() => {
    if (highlightId) {
      const timer = setTimeout(() => setHighlightActive(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [highlightId]);

  // Filter + sort
  const filteredAndSorted = useMemo(() => {
    let result = [...allTransactions];

    if (statusFilter) {
      result = result.filter((t) => t.status === statusFilter);
    }
    if (typeFilter) {
      result = result.filter((t) => t.transactionType === typeFilter);
    }
    if (accountSearch) {
      result = result.filter((t) => t.accountNumber.includes(accountSearch));
    }
    if (startDate) {
      result = result.filter((t) => t.transactionDate >= startDate);
    }
    if (endDate) {
      result = result.filter((t) => t.transactionDate <= endDate);
    }

    result.sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      if (aVal === undefined && bVal === undefined) return 0;
      if (aVal === undefined) return 1;
      if (bVal === undefined) return -1;
      if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });

    return result;
  }, [allTransactions, statusFilter, typeFilter, accountSearch, startDate, endDate, sortField, sortDir]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filteredAndSorted.length / PAGE_SIZE));
  const paginatedData = filteredAndSorted.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('asc');
    }
    setCurrentPage(1);
  };

  const handleRowClick = (txId: string) => {
    setExpandedRow((prev) => (prev === txId ? null : txId));
  };

  const sortIndicator = (field: SortField) => {
    if (sortField !== field) return ' \u2195';
    return sortDir === 'asc' ? ' \u2191' : ' \u2193';
  };

  const resetFilters = () => {
    setStatusFilter('');
    setTypeFilter('');
    setAccountSearch('');
    setStartDate('');
    setEndDate('');
    setCurrentPage(1);
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
            {/* Filter bar */}
            <Card hover={false} className="animate-fade-in" padding="sm">
              <div className="grid gap-4 md:grid-cols-5">
                <div>
                  <label htmlFor="statusFilter" className="block text-xs font-medium mb-1 text-muted-foreground">
                    Status
                  </label>
                  <select
                    id="statusFilter"
                    value={statusFilter}
                    onChange={(e) => { setStatusFilter(e.target.value as TxStatus | ''); setCurrentPage(1); }}
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
                  <label htmlFor="typeFilter" className="block text-xs font-medium mb-1 text-muted-foreground">
                    Type
                  </label>
                  <select
                    id="typeFilter"
                    value={typeFilter}
                    onChange={(e) => { setTypeFilter(e.target.value as TransactionType | ''); setCurrentPage(1); }}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                  >
                    <option value="">All Types</option>
                    <option value="BU">Buy</option>
                    <option value="SL">Sell</option>
                    <option value="TR">Transfer</option>
                    <option value="FE">Fee</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="accountSearch" className="block text-xs font-medium mb-1 text-muted-foreground">
                    Account
                  </label>
                  <Input
                    id="accountSearch"
                    placeholder="Search account..."
                    value={accountSearch}
                    onChange={(e) => { setAccountSearch(e.target.value); setCurrentPage(1); }}
                  />
                </div>
                <div>
                  <label htmlFor="startDate" className="block text-xs font-medium mb-1 text-muted-foreground">
                    From Date
                  </label>
                  <Input
                    id="startDate"
                    type="date"
                    value={startDate}
                    onChange={(e) => { setStartDate(e.target.value); setCurrentPage(1); }}
                  />
                </div>
                <div>
                  <label htmlFor="endDate" className="block text-xs font-medium mb-1 text-muted-foreground">
                    To Date
                  </label>
                  <Input
                    id="endDate"
                    type="date"
                    value={endDate}
                    onChange={(e) => { setEndDate(e.target.value); setCurrentPage(1); }}
                  />
                </div>
              </div>
              <div className="mt-3 flex justify-end">
                <button
                  onClick={resetFilters}
                  className="text-xs text-muted-foreground hover:text-foreground underline"
                >
                  Reset filters
                </button>
              </div>
            </Card>

            {/* Transaction table */}
            <Card hover={false} className="animate-fade-in" padding="sm">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="cursor-pointer select-none" onClick={() => handleSort('transactionId')}>
                      ID{sortIndicator('transactionId')}
                    </TableHead>
                    <TableHead className="cursor-pointer select-none" onClick={() => handleSort('transactionDate')}>
                      Date{sortIndicator('transactionDate')}
                    </TableHead>
                    <TableHead className="cursor-pointer select-none" onClick={() => handleSort('transactionType')}>
                      Type{sortIndicator('transactionType')}
                    </TableHead>
                    <TableHead className="cursor-pointer select-none" onClick={() => handleSort('accountNumber')}>
                      Account{sortIndicator('accountNumber')}
                    </TableHead>
                    <TableHead className="cursor-pointer select-none" onClick={() => handleSort('fundId')}>
                      Fund ID{sortIndicator('fundId')}
                    </TableHead>
                    <TableHead className="cursor-pointer select-none text-right" onClick={() => handleSort('quantity')}>
                      Quantity{sortIndicator('quantity')}
                    </TableHead>
                    <TableHead className="cursor-pointer select-none text-right" onClick={() => handleSort('price')}>
                      Price{sortIndicator('price')}
                    </TableHead>
                    <TableHead className="cursor-pointer select-none text-right" onClick={() => handleSort('amount')}>
                      Amount{sortIndicator('amount')}
                    </TableHead>
                    <TableHead className="cursor-pointer select-none" onClick={() => handleSort('status')}>
                      Status{sortIndicator('status')}
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paginatedData.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                        No transactions found matching the current filters.
                      </TableCell>
                    </TableRow>
                  ) : (
                    paginatedData.map((tx) => {
                      const isHighlighted = highlightActive && tx.transactionId === highlightId;
                      const isExpanded = expandedRow === tx.transactionId;

                      return (
                        <React.Fragment key={tx.transactionId}>
                          <TableRow
                            className={`cursor-pointer ${isHighlighted ? 'animate-pulse bg-primary/10' : ''}`}
                            onClick={() => handleRowClick(tx.transactionId)}
                          >
                            <TableCell className="font-mono text-xs">{tx.transactionId}</TableCell>
                            <TableCell>{tx.transactionDate}</TableCell>
                            <TableCell>{TRANSACTION_TYPE_LABELS[tx.transactionType]}</TableCell>
                            <TableCell className="font-mono text-xs">{tx.accountNumber}</TableCell>
                            <TableCell className="font-mono text-xs">{tx.fundId || '—'}</TableCell>
                            <TableCell className="text-right">{tx.quantity > 0 ? tx.quantity.toFixed(4) : '—'}</TableCell>
                            <TableCell className="text-right">{tx.price > 0 ? `$${tx.price.toFixed(2)}` : '—'}</TableCell>
                            <TableCell className="text-right font-medium">${tx.amount.toFixed(2)}</TableCell>
                            <TableCell>
                              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${STATUS_COLORS[tx.status]}`}>
                                {STATUS_LABELS[tx.status]}
                              </span>
                            </TableCell>
                          </TableRow>

                          {/* Expanded detail row */}
                          {isExpanded && (
                            <TableRow>
                              <TableCell colSpan={9} className="bg-muted/30 p-4">
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                  <div>
                                    <span className="text-muted-foreground block text-xs">Transaction ID</span>
                                    <span className="font-mono">{tx.transactionId}</span>
                                  </div>
                                  <div>
                                    <span className="text-muted-foreground block text-xs">Type</span>
                                    <span>{TRANSACTION_TYPE_LABELS[tx.transactionType]} ({tx.transactionType})</span>
                                  </div>
                                  <div>
                                    <span className="text-muted-foreground block text-xs">Portfolio ID</span>
                                    <span className="font-mono">{tx.portfolioId}</span>
                                  </div>
                                  <div>
                                    <span className="text-muted-foreground block text-xs">Currency</span>
                                    <span>{tx.currency}</span>
                                  </div>
                                  <div>
                                    <span className="text-muted-foreground block text-xs">Account</span>
                                    <span className="font-mono">{tx.accountNumber}</span>
                                  </div>
                                  <div>
                                    <span className="text-muted-foreground block text-xs">Fund ID</span>
                                    <span className="font-mono">{tx.fundId || '—'}</span>
                                  </div>
                                  <div>
                                    <span className="text-muted-foreground block text-xs">Quantity</span>
                                    <span>{tx.quantity > 0 ? tx.quantity.toFixed(4) : '—'}</span>
                                  </div>
                                  <div>
                                    <span className="text-muted-foreground block text-xs">Price</span>
                                    <span>{tx.price > 0 ? `$${tx.price.toFixed(4)}` : '—'}</span>
                                  </div>
                                  <div>
                                    <span className="text-muted-foreground block text-xs">Amount</span>
                                    <span className="font-semibold">${tx.amount.toFixed(2)}</span>
                                  </div>
                                  <div>
                                    <span className="text-muted-foreground block text-xs">Date</span>
                                    <span>{tx.transactionDate}</span>
                                  </div>
                                  <div>
                                    <span className="text-muted-foreground block text-xs">Status</span>
                                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${STATUS_COLORS[tx.status]}`}>
                                      {STATUS_LABELS[tx.status]}
                                    </span>
                                  </div>
                                  {tx.sourceAccount && (
                                    <div>
                                      <span className="text-muted-foreground block text-xs">Source Account</span>
                                      <span className="font-mono">{tx.sourceAccount}</span>
                                    </div>
                                  )}
                                  {tx.destinationAccount && (
                                    <div>
                                      <span className="text-muted-foreground block text-xs">Destination Account</span>
                                      <span className="font-mono">{tx.destinationAccount}</span>
                                    </div>
                                  )}
                                  {tx.description && (
                                    <div className="col-span-2">
                                      <span className="text-muted-foreground block text-xs">Description</span>
                                      <span>{tx.description}</span>
                                    </div>
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

              {/* Pagination */}
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
                <p className="text-sm text-muted-foreground">
                  Showing {filteredAndSorted.length === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1}–{Math.min(currentPage * PAGE_SIZE, filteredAndSorted.length)} of {filteredAndSorted.length} transactions
                </p>
                <div className="flex gap-2 items-center">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={currentPage <= 1}
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-muted-foreground">
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
            </Card>
          </main>
        </div>
      </Container>
    </div>
  );
}
