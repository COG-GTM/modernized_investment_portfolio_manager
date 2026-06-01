import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { portfolioApi, ApiError } from '../services/api';
import { useToast } from '../contexts/ToastContext';
import Container from '../components/Container';
import PageHeader from '../components/PageHeader';
import Card from '../components/Card';
import Button from '../components/Button';
import SkeletonLoader from '../components/SkeletonLoader';
import Pagination from '../components/Pagination';
import type { Transaction } from '../types';
import { portfolioPath } from '../types/routes';
import { formatCurrency, formatNumber, formatDate } from '../utils/format';

const PAGE_SIZE = 10;

export default function TransactionHistory() {
  const { id } = useParams<{ id: string }>();
  const { addToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [message, setMessage] = useState('');

  const loadHistory = useCallback(
    async (page: number) => {
      if (!id) return;
      setLoading(true);
      setError(null);

      try {
        const data = await portfolioApi.getHistory(id, page, PAGE_SIZE);
        setTransactions(data.transactions);
        setCurrentPage(data.currentPage);
        setTotalPages(data.totalPages);
        setTotalItems(data.totalItems);
        setMessage(data.message);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
          addToast(err.message, 'error');
        } else {
          setError('An unexpected error occurred while loading transactions.');
          addToast('Failed to load transaction history', 'error');
        }
      } finally {
        setLoading(false);
      }
    },
    [id, addToast]
  );

  useEffect(() => {
    loadHistory(1);
  }, [loadHistory]);

  const handlePageChange = (page: number) => {
    loadHistory(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="md">
        <div className="space-y-8">
          <div className="flex items-center gap-4">
            <Link to="/">
              <Button variant="secondary" size="sm">← Main Menu</Button>
            </Link>
            {id && (
              <Link to={portfolioPath(id)}>
                <Button variant="outline" size="sm">← Back to Portfolio</Button>
              </Link>
            )}
          </div>

          <PageHeader
            title="Transaction History Inquiry"
            subtitle={id ? `Account: ${id}` : 'Review your investment transaction activity'}
          />

          <main className="space-y-6 animate-slide-up">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm" role="alert">
                {error}
              </div>
            )}

            <Card className="animate-fade-in">
              <h2 className="text-2xl font-semibold mb-4">
                {id ? `Transactions for Account ${id}` : 'Recent Transactions'}
              </h2>

              {loading ? (
                <div className="space-y-4">
                  <SkeletonLoader lines={3} />
                  <SkeletonLoader lines={1} height="h-2" />
                  <SkeletonLoader lines={5} />
                </div>
              ) : transactions.length === 0 ? (
                <div className="text-center py-8 space-y-4">
                  <p className="text-muted-foreground">No transactions found for this account.</p>
                  <div className="text-sm text-muted-foreground space-y-2 max-w-xs mx-auto text-left">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-primary rounded-full" />
                      <span>Buy/sell transactions</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-primary rounded-full" />
                      <span>Dividend payments</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-primary rounded-full" />
                      <span>Fee and commission details</span>
                    </div>
                  </div>
                </div>
              ) : (
                <>
                  {message && (
                    <p className="text-muted-foreground text-sm mb-4">{message}</p>
                  )}

                  <p className="text-sm text-muted-foreground mb-4">
                    Showing {transactions.length} of {totalItems} transactions
                  </p>

                  {/* Table header - maps to HISMAP column headers */}
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm" role="table">
                      <thead>
                        <tr className="border-b-2 border-border">
                          <th className="text-left py-3 px-2 font-bold">Date</th>
                          <th className="text-left py-3 px-2 font-bold">Type</th>
                          <th className="text-right py-3 px-2 font-bold">Units</th>
                          <th className="text-right py-3 px-2 font-bold">Price</th>
                          <th className="text-right py-3 px-2 font-bold">Amount</th>
                        </tr>
                      </thead>
                      <tbody>
                        {transactions.map((tx, index) => (
                          <tr
                            key={`${tx.transactionId ?? index}`}
                            className="border-b border-border hover:bg-muted/50 transition-fast"
                          >
                            <td className="py-3 px-2">{formatDate(tx.date)}</td>
                            <td className="py-3 px-2">
                              <span
                                className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${
                                  tx.type === 'BY' || tx.type === 'BUY'
                                    ? 'bg-green-100 text-green-800'
                                    : tx.type === 'SL' || tx.type === 'SELL'
                                      ? 'bg-red-100 text-red-800'
                                      : 'bg-gray-100 text-gray-800'
                                }`}
                              >
                                {tx.type}
                              </span>
                            </td>
                            <td className="py-3 px-2 text-right font-mono">
                              {formatNumber(tx.units, 3)}
                            </td>
                            <td className="py-3 px-2 text-right font-mono">
                              {formatCurrency(tx.price)}
                            </td>
                            <td className="py-3 px-2 text-right font-mono font-medium">
                              {formatCurrency(tx.amount)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={handlePageChange}
                    className="mt-6"
                  />
                </>
              )}
            </Card>

            <div className="flex justify-center animate-fade-in" style={{ animationDelay: '200ms' }}>
              <Link to="/">
                <Button variant="outline">PF3 Exit to Menu</Button>
              </Link>
            </div>
          </main>
        </div>
      </Container>
    </div>
  );
}
