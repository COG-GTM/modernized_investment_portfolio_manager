import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button, SkeletonLoader, Alert } from '../components';
import { fetchInquiryHistory, ApiError } from '../services/api';
import type { HistoryInquiryResponse, TransactionRecord } from '../types/account';
import { formatCurrency } from '../utils/format';

const ROWS_PER_PAGE = 10;

const TYPE_LABELS: Record<string, string> = {
  BU: 'Buy',
  SL: 'Sell',
  TR: 'Transfer',
  FE: 'Fee',
};

const STATUS_LABELS: Record<string, string> = {
  A: 'Active',
  C: 'Closed',
  P: 'Pending',
  D: 'Done',
  F: 'Failed',
};

function getTypeLabel(code: string): string {
  return TYPE_LABELS[code] || code;
}

function getStatusLabel(code: string): string {
  return STATUS_LABELS[code] || code;
}

function getTypeBadgeClass(code: string): string {
  switch (code) {
    case 'BU':
      return 'bg-green-100 text-green-800';
    case 'SL':
      return 'bg-red-100 text-red-800';
    case 'TR':
      return 'bg-blue-100 text-blue-800';
    case 'FE':
      return 'bg-yellow-100 text-yellow-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export default function TransactionHistory() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [historyData, setHistoryData] = useState<HistoryInquiryResponse | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const location = useLocation();

  useEffect(() => {
    const loadTransactions = async () => {
      const urlParams = new URLSearchParams(location.search);
      const accountNumber = urlParams.get('account');

      if (!accountNumber) {
        setLoading(false);
        return;
      }

      try {
        const data = await fetchInquiryHistory(accountNumber);
        setHistoryData(data);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError('An unexpected error occurred while loading transactions.');
        }
      } finally {
        setLoading(false);
      }
    };

    setCurrentPage(0);
    loadTransactions();
  }, [location.search]);

  const totalPages = historyData
    ? Math.ceil(historyData.transactions.length / ROWS_PER_PAGE)
    : 0;

  const paginatedTransactions: TransactionRecord[] = historyData
    ? historyData.transactions.slice(
        currentPage * ROWS_PER_PAGE,
        (currentPage + 1) * ROWS_PER_PAGE
      )
    : [];

  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="md">
        <div className="space-y-8">
          <div className="flex items-center justify-between">
            <Link to={ROUTES.MAIN_MENU}>
              <Button variant="secondary" size="sm">
                ← Back to Main Menu
              </Button>
            </Link>
          </div>
          <PageHeader
            title="Transaction History Inquiry"
            subtitle="Review your investment transaction activity"
          />

          <main className="space-y-6 animate-slide-up">
            {error && (
              <Alert variant="destructive" className="animate-fade-in">
                {error}
              </Alert>
            )}

            <Card hover className="animate-fade-in">
              <h2 className="text-2xl font-semibold mb-4">
                {historyData
                  ? `Transactions for Account ${historyData.account_number}`
                  : 'Recent Transactions'}
              </h2>
              {loading ? (
                <div className="space-y-4">
                  <SkeletonLoader lines={3} />
                  <SkeletonLoader lines={1} height="h-2" />
                </div>
              ) : historyData ? (
                <>
                  {historyData.message && (
                    <p className="text-muted-foreground mb-4">
                      {historyData.message}
                    </p>
                  )}
                  {historyData.transactions.length === 0 ? (
                    <p className="text-muted-foreground text-center py-4">
                      No transactions found for this account.
                    </p>
                  ) : (
                    <>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-left py-3 px-2 font-semibold">Date</th>
                              <th className="text-left py-3 px-2 font-semibold">Type</th>
                              <th className="text-right py-3 px-2 font-semibold">Units</th>
                              <th className="text-right py-3 px-2 font-semibold">Price</th>
                              <th className="text-right py-3 px-2 font-semibold">Amount</th>
                              <th className="text-center py-3 px-2 font-semibold">Status</th>
                            </tr>
                          </thead>
                          <tbody>
                            {paginatedTransactions.map((txn) => (
                              <tr
                                key={`${txn.sequence_no}-${txn.date}`}
                                className="border-b last:border-b-0 hover:bg-muted/50 transition-colors"
                              >
                                <td className="py-3 px-2">
                                  <div>{txn.date}</div>
                                  <div className="text-xs text-muted-foreground">{txn.time}</div>
                                </td>
                                <td className="py-3 px-2">
                                  <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${getTypeBadgeClass(txn.type)}`}>
                                    {getTypeLabel(txn.type)}
                                  </span>
                                </td>
                                <td className="py-3 px-2 text-right font-medium">
                                  {txn.quantity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                </td>
                                <td className="py-3 px-2 text-right font-medium">
                                  {formatCurrency(txn.price)}
                                </td>
                                <td className="py-3 px-2 text-right font-medium">
                                  {formatCurrency(txn.amount)}
                                </td>
                                <td className="py-3 px-2 text-center">
                                  <span className="text-xs text-muted-foreground">
                                    {getStatusLabel(txn.status)}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {totalPages > 1 && (
                        <div className="flex justify-between items-center pt-4 border-t mt-4">
                          <p className="text-sm text-muted-foreground">
                            Page {currentPage + 1} of {totalPages} ({historyData.transactions.length} total)
                          </p>
                          <div className="flex gap-2">
                            <Button
                              variant="secondary"
                              size="sm"
                              disabled={currentPage === 0}
                              onClick={() => setCurrentPage((p) => p - 1)}
                            >
                              ← Previous (PF7)
                            </Button>
                            <Button
                              variant="secondary"
                              size="sm"
                              disabled={currentPage >= totalPages - 1}
                              onClick={() => setCurrentPage((p) => p + 1)}
                            >
                              Next (PF8) →
                            </Button>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </>
              ) : (
                <>
                  <p className="text-muted-foreground mb-4">
                    This page will display a comprehensive list of all investment transactions
                    including purchases, sales, dividends, and other portfolio activities.
                  </p>
                  <p className="text-sm text-muted-foreground mb-4">
                    To view transactions, navigate here from a portfolio inquiry or provide an account number in the URL.
                  </p>
                </>
              )}
            </Card>

            <div className="flex justify-center animate-fade-in" style={{ animationDelay: '200ms' }}>
              <Link to={ROUTES.PORTFOLIO_INQUIRY}>
                <Button variant="primary">
                  View Portfolio
                </Button>
              </Link>
            </div>
          </main>
        </div>
      </Container>
    </div>
  );
}
