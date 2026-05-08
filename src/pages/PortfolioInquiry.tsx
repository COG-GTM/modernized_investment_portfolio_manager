import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button, Alert } from '../components';
import { AccountInput } from '../components/AccountInput';
import { accountFormSchema, type AccountFormData, type PortfolioInquiryResponse, type InquiryPosition } from '../types/account';
import { fetchInquiryPortfolio, ApiError } from '../services/api';
import { formatCurrency, formatNumber, formatPercentage, getGainLossColorClass, formatLastUpdated } from '../utils/format';

const POSITIONS_PER_PAGE = 5;

const STATUS_LABELS: Record<string, string> = {
  A: 'Active',
  C: 'Closed',
  P: 'Pending',
  D: 'Done',
  F: 'Failed',
};

function getStatusLabel(code: string): string {
  return STATUS_LABELS[code] || code;
}

function getStatusBadgeClass(code: string): string {
  switch (code) {
    case 'A':
      return 'bg-green-100 text-green-800';
    case 'C':
      return 'bg-gray-100 text-gray-800';
    case 'P':
      return 'bg-yellow-100 text-yellow-800';
    case 'D':
      return 'bg-blue-100 text-blue-800';
    case 'F':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export default function PortfolioInquiry() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [portfolioData, setPortfolioData] = useState<PortfolioInquiryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(0);

  const methods = useForm<AccountFormData>({
    resolver: zodResolver(accountFormSchema),
    mode: 'onChange',
    defaultValues: {
      accountNumber: '',
    },
  });

  const { handleSubmit, formState: { isValid } } = methods;

  const onSubmit = async (data: AccountFormData) => {
    setIsSubmitting(true);
    setError(null);
    setCurrentPage(0);

    try {
      const portfolio = await fetchInquiryPortfolio(data.accountNumber);
      setPortfolioData(portfolio);
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
      handleSubmit(onSubmit)();
    }
  };

  const resetForm = () => {
    setPortfolioData(null);
    setError(null);
    setCurrentPage(0);
    methods.reset();
  };

  const totalPages = portfolioData
    ? Math.ceil(portfolioData.positions.length / POSITIONS_PER_PAGE)
    : 0;

  const paginatedPositions: InquiryPosition[] = portfolioData
    ? portfolioData.positions.slice(
        currentPage * POSITIONS_PER_PAGE,
        (currentPage + 1) * POSITIONS_PER_PAGE
      )
    : [];

  if (portfolioData) {
    const summary = portfolioData.portfolio_summary;

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
              <Button variant="secondary" size="sm" onClick={resetForm}>
                New Search
              </Button>
            </div>
            <PageHeader
              title="Portfolio Position Inquiry"
              subtitle={`Account: ${portfolioData.account_number}`}
            />

            <main className="space-y-6 animate-slide-up">
              {portfolioData.message && (
                <Alert className="animate-fade-in">
                  {portfolioData.message}
                </Alert>
              )}

              <Card hover className="animate-fade-in">
                <div className="space-y-6">
                  <div className="flex justify-between items-start">
                    <div>
                      <h2 className="text-2xl font-semibold">Portfolio Summary</h2>
                      <p className="text-sm text-muted-foreground">
                        {summary.client_name}
                      </p>
                    </div>
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeClass(summary.status)}`}>
                      {getStatusLabel(summary.status)}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-primary/5 rounded-lg p-4">
                      <p className="text-sm text-muted-foreground">Total Value</p>
                      <p className="text-2xl font-bold">
                        {formatCurrency(summary.total_value)}
                      </p>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-4">
                      <p className="text-sm text-muted-foreground">Cash Balance</p>
                      <p className="text-2xl font-bold">
                        {formatCurrency(summary.cash_balance)}
                      </p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4">
                      <p className="text-sm text-muted-foreground">Portfolio ID</p>
                      <p className="text-2xl font-bold">{summary.portfolio_id}</p>
                    </div>
                  </div>
                </div>
              </Card>

              <div className="space-y-4 animate-fade-in" style={{ animationDelay: '100ms' }}>
                <div className="flex justify-between items-center">
                  <h3 className="text-xl font-semibold">
                    Positions ({portfolioData.positions.length})
                  </h3>
                  {totalPages > 1 && (
                    <p className="text-sm text-muted-foreground">
                      Page {currentPage + 1} of {totalPages}
                    </p>
                  )}
                </div>

                {paginatedPositions.length === 0 ? (
                  <Card>
                    <p className="text-muted-foreground text-center py-4">
                      No positions found for this account.
                    </p>
                  </Card>
                ) : (
                  <div className="grid gap-4">
                    {paginatedPositions.map((position, index) => {
                      const gainLossColor = getGainLossColorClass(position.gain_loss);
                      return (
                        <Card
                          key={`${position.investment_id}-${position.date}`}
                          hover
                          className="animate-fade-in"
                          style={{ animationDelay: `${100 + index * 50}ms` }}
                        >
                          <div className="space-y-4">
                            <div className="flex justify-between items-start">
                              <div>
                                <h3 className="text-lg font-semibold">{position.investment_id}</h3>
                                <p className="text-sm text-muted-foreground">
                                  Date: {position.date} | {position.currency}
                                </p>
                              </div>
                              <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeClass(position.status)}`}>
                                {getStatusLabel(position.status)}
                              </span>
                            </div>

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              <div>
                                <p className="text-sm text-muted-foreground">Units</p>
                                <p className="font-medium">{formatNumber(position.quantity, 2)}</p>
                              </div>
                              <div>
                                <p className="text-sm text-muted-foreground">Cost Basis</p>
                                <p className="font-medium">{formatCurrency(position.cost_basis, position.currency)}</p>
                              </div>
                              <div>
                                <p className="text-sm text-muted-foreground">Market Value</p>
                                <p className="font-medium">{formatCurrency(position.market_value, position.currency)}</p>
                              </div>
                              <div>
                                <p className="text-sm text-muted-foreground">Last Maintained</p>
                                <p className="font-medium text-sm">{formatLastUpdated(position.last_maint_date)}</p>
                              </div>
                            </div>

                            <div className="pt-2 border-t">
                              <div className="flex justify-between items-center">
                                <span className="text-sm text-muted-foreground">Gain/Loss</span>
                                <span className={`font-semibold ${gainLossColor}`}>
                                  {position.gain_loss >= 0 ? '+' : ''}{formatCurrency(position.gain_loss, position.currency)} ({position.gain_loss_percent >= 0 ? '+' : ''}{formatPercentage(position.gain_loss_percent)})
                                </span>
                              </div>
                            </div>
                          </div>
                        </Card>
                      );
                    })}
                  </div>
                )}

                {totalPages > 1 && (
                  <div className="flex justify-center gap-4 pt-2">
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
                )}
              </div>

              <div className="flex justify-center animate-fade-in" style={{ animationDelay: '200ms' }}>
                <Link to={`${ROUTES.TRANSACTION_HISTORY}?account=${portfolioData.account_number}`}>
                  <Button variant="primary">
                    View Transaction History
                  </Button>
                </Link>
              </div>
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
            title="Portfolio Position Inquiry"
            subtitle="Enter your account number to view portfolio positions"
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

                  <Button
                    type="submit"
                    disabled={!isValid || isSubmitting}
                    className="w-full"
                  >
                    {isSubmitting ? 'Searching...' : 'View Portfolio'}
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
