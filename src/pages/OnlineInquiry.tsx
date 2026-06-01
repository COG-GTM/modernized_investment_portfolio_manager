import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button, Alert } from '../components';
import { AccountInput } from '../components/AccountInput';
import { inquiryFormSchema, type InquiryFormData, type InquiryTab, type PortfolioInquiryResult, type TransactionHistoryResult } from '../types/inquiry';
import { fetchPortfolioInquiry, fetchTransactionHistoryInquiry, ApiError } from '../services/inquiryApi';
import { formatCurrency, formatNumber, getGainLossColorClass } from '../utils/format';

export default function OnlineInquiry() {
  const [activeTab, setActiveTab] = useState<InquiryTab>('portfolio');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [portfolioData, setPortfolioData] = useState<PortfolioInquiryResult | null>(null);
  const [historyData, setHistoryData] = useState<TransactionHistoryResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const methods = useForm<InquiryFormData>({
    resolver: zodResolver(inquiryFormSchema),
    mode: 'onChange',
    defaultValues: {
      accountNumber: '',
    },
  });

  const { handleSubmit, formState: { isValid } } = methods;

  const onSubmit = async (data: InquiryFormData) => {
    setIsSubmitting(true);
    setError(null);

    try {
      if (activeTab === 'portfolio') {
        const result = await fetchPortfolioInquiry(data.accountNumber);
        setPortfolioData(result);
        setHistoryData(null);
      } else {
        const result = await fetchTransactionHistoryInquiry(data.accountNumber);
        setHistoryData(result);
        setPortfolioData(null);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && isValid && !isSubmitting) {
      event.preventDefault();
      handleSubmit(onSubmit)();
    }
  };

  const resetForm = () => {
    setPortfolioData(null);
    setHistoryData(null);
    setError(null);
    methods.reset();
  };

  if (portfolioData) {
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
              <Button variant="outline" size="sm" onClick={resetForm}>
                New Search
              </Button>
            </div>
            <PageHeader
              title="Portfolio Positions"
              subtitle={`Account: ${portfolioData.accountNumber}`}
            />

            <main className="space-y-6 animate-slide-up">
              <Card hover className="animate-fade-in">
                <div className="space-y-6">
                  <h2 className="text-2xl font-semibold">Portfolio Summary</h2>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-primary/5 rounded-lg p-4">
                      <p className="text-sm text-muted-foreground">Total Value</p>
                      <p className="text-2xl font-bold">
                        {formatCurrency(portfolioData.totalValue, portfolioData.currency)}
                      </p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4">
                      <p className="text-sm text-muted-foreground">Total Gain/Loss</p>
                      <p className={`text-2xl font-bold ${getGainLossColorClass(portfolioData.totalGainLoss)}`}>
                        {formatCurrency(portfolioData.totalGainLoss, portfolioData.currency)}
                      </p>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-4">
                      <p className="text-sm text-muted-foreground">Cash Balance</p>
                      <p className="text-2xl font-bold">
                        {formatCurrency(portfolioData.cashBalance, portfolioData.currency)}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
                    <div>
                      <p className="text-sm text-muted-foreground">Portfolio ID</p>
                      <p className="font-medium">{portfolioData.portfolioId}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Client Name</p>
                      <p className="font-medium">{portfolioData.clientName || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Status</p>
                      <p className="font-medium">{portfolioData.status || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Total Cost Basis</p>
                      <p className="font-medium">{formatCurrency(portfolioData.totalCostBasis, portfolioData.currency)}</p>
                    </div>
                  </div>
                </div>
              </Card>

              <div className="space-y-4 animate-fade-in" style={{ animationDelay: '100ms' }}>
                <h3 className="text-xl font-semibold">Positions ({portfolioData.positions.length})</h3>
                <div className="grid gap-4">
                  {portfolioData.positions.map((position, index) => (
                    <Card
                      key={`${position.investmentId}-${index}`}
                      hover
                      className="animate-fade-in"
                      style={{ animationDelay: `${100 + (index * 50)}ms` }}
                    >
                      <div className="space-y-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <h3 className="text-lg font-semibold">{position.investmentId}</h3>
                            <p className="text-sm text-muted-foreground">
                              {position.status} | {position.currency}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm text-muted-foreground">Gain/Loss</p>
                            <span className={`font-semibold ${getGainLossColorClass(position.gainLoss)}`}>
                              {formatCurrency(position.gainLoss, position.currency)} ({position.gainLossPercent >= 0 ? '+' : ''}{formatNumber(position.gainLossPercent)}%)
                            </span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div>
                            <p className="text-sm text-muted-foreground">Quantity</p>
                            <p className="font-medium">{formatNumber(position.quantity, 0)}</p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">Cost Basis</p>
                            <p className="font-medium">{formatCurrency(position.costBasis, position.currency)}</p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">Market Value</p>
                            <p className="font-medium">{formatCurrency(position.marketValue, position.currency)}</p>
                          </div>
                          <div>
                            <p className="text-sm text-muted-foreground">Position Date</p>
                            <p className="font-medium">{position.positionDate || 'N/A'}</p>
                          </div>
                        </div>
                      </div>
                    </Card>
                  ))}
                  {portfolioData.positions.length === 0 && (
                    <Card>
                      <p className="text-center text-muted-foreground">No positions found for this account.</p>
                    </Card>
                  )}
                </div>
              </div>
            </main>
          </div>
        </Container>
      </div>
    );
  }

  if (historyData) {
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
              <Button variant="outline" size="sm" onClick={resetForm}>
                New Search
              </Button>
            </div>
            <PageHeader
              title="Transaction History"
              subtitle={`Account: ${historyData.accountNumber} | Portfolio: ${historyData.portfolioId}`}
            />

            <main className="space-y-6 animate-slide-up">
              <Card hover className="animate-fade-in">
                <h2 className="text-2xl font-semibold mb-2">Transactions</h2>
                <p className="text-sm text-muted-foreground mb-4">
                  {historyData.message} ({historyData.totalEntries} total entries)
                </p>

                {historyData.entries.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-3 px-2 font-semibold">Date</th>
                          <th className="text-left py-3 px-2 font-semibold">Type</th>
                          <th className="text-right py-3 px-2 font-semibold">Units</th>
                          <th className="text-right py-3 px-2 font-semibold">Price</th>
                          <th className="text-right py-3 px-2 font-semibold">Amount</th>
                        </tr>
                      </thead>
                      <tbody>
                        {historyData.entries.map((entry, index) => (
                          <tr
                            key={index}
                            className="border-b last:border-b-0 animate-fade-in"
                            style={{ animationDelay: `${index * 30}ms` }}
                          >
                            <td className="py-3 px-2">{entry.transactionDate || 'N/A'}</td>
                            <td className="py-3 px-2">
                              <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${
                                entry.transactionType === 'BUY'
                                  ? 'bg-green-100 text-green-800'
                                  : entry.transactionType === 'SELL'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-gray-100 text-gray-800'
                              }`}>
                                {entry.transactionType}
                              </span>
                            </td>
                            <td className="py-3 px-2 text-right">{formatNumber(entry.quantity, 0)}</td>
                            <td className="py-3 px-2 text-right">{formatCurrency(entry.price)}</td>
                            <td className={`py-3 px-2 text-right font-medium ${getGainLossColorClass(entry.amount)}`}>
                              {formatCurrency(entry.amount)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-center text-muted-foreground py-4">No transaction history found.</p>
                )}

                {historyData.hasMore && (
                  <p className="text-sm text-muted-foreground text-center mt-4">
                    Showing first {historyData.entries.length} of {historyData.totalEntries} entries.
                  </p>
                )}
              </Card>
            </main>
          </div>
        </Container>
      </div>
    );
  }

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
            title="Online Inquiry"
            subtitle="Access portfolio positions and transaction history"
          />

          <main className="space-y-6 animate-slide-up">
            {error && (
              <Alert variant="destructive" className="animate-fade-in">
                {error}
              </Alert>
            )}

            <Card hover className="animate-fade-in">
              <FormProvider {...methods}>
                <form onSubmit={handleSubmit(onSubmit)} onKeyDown={handleKeyDown} className="space-y-6">
                  <div>
                    <h2 className="text-2xl font-semibold mb-4">Account Search</h2>
                    <AccountInput />
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">Inquiry Type</label>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setActiveTab('portfolio')}
                        className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-smooth ${
                          activeTab === 'portfolio'
                            ? 'bg-primary text-primary-foreground shadow-sm'
                            : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                        }`}
                      >
                        Portfolio Positions
                      </button>
                      <button
                        type="button"
                        onClick={() => setActiveTab('history')}
                        className={`flex-1 py-2 px-4 text-sm font-medium rounded-md transition-smooth ${
                          activeTab === 'history'
                            ? 'bg-primary text-primary-foreground shadow-sm'
                            : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                        }`}
                      >
                        Transaction History
                      </button>
                    </div>
                  </div>

                  <Button
                    type="submit"
                    disabled={!isValid || isSubmitting}
                    className="w-full"
                  >
                    {isSubmitting
                      ? 'Searching...'
                      : activeTab === 'portfolio'
                      ? 'View Portfolio Positions'
                      : 'View Transaction History'}
                  </Button>
                </form>
              </FormProvider>
            </Card>
          </main>
        </div>
      </Container>
    </div>
  );
}
