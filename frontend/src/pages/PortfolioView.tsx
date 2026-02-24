import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { portfolioApi, ApiError } from '../services/api';
import { useToast } from '../contexts/ToastContext';
import Container from '../components/Container';
import PageHeader from '../components/PageHeader';
import Card from '../components/Card';
import Button from '../components/Button';
import PositionCard from '../components/PositionCard';
import PortfolioSummaryCard from '../components/PortfolioSummaryCard';
import SkeletonLoader from '../components/SkeletonLoader';
import type { PortfolioSummary, Portfolio } from '../types';
import { historyPath } from '../types/routes';

export default function PortfolioView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addToast } = useToast();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [portfolioData, setPortfolioData] = useState<PortfolioSummary | null>(null);

  // If id is 'lookup', show account search form
  const isLookupMode = id === 'lookup';
  const [accountInput, setAccountInput] = useState('');
  const [inputError, setInputError] = useState<string | null>(null);

  useEffect(() => {
    if (!isLookupMode && id) {
      loadPortfolio(id);
    }
  }, [id, isLookupMode]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadPortfolio = async (accountId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await portfolioApi.getPortfolio(accountId);
      setPortfolioData(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
        addToast(err.message, 'error');
      } else {
        setError('An unexpected error occurred while fetching portfolio data.');
        addToast('Failed to load portfolio', 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLookup = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = accountInput.trim();
    if (!trimmed) {
      setInputError('Please enter an account number.');
      return;
    }
    if (!/^\d+$/.test(trimmed)) {
      setInputError('Account number must contain only numeric characters.');
      return;
    }
    setInputError(null);
    navigate(`/portfolios/${trimmed}`);
  };

  const handleNewSearch = () => {
    setPortfolioData(null);
    setError(null);
    setAccountInput('');
    navigate('/portfolios/lookup');
  };

  // Map PortfolioSummary to Portfolio type for display
  const toPortfolio = (data: PortfolioSummary): Portfolio => ({
    portfolioId: `PF-${data.accountNumber}`,
    accountNumber: data.accountNumber,
    totalValue: data.totalValue,
    totalCostBasis: data.totalValue - data.totalGainLoss,
    totalGainLoss: data.totalGainLoss,
    totalGainLossPercent: data.totalGainLossPercent,
    currency: 'USD',
    positions: data.holdings.map((h) => ({
      portfolioId: `PF-${data.accountNumber}`,
      investmentId: `INV-${h.symbol}-001`,
      symbol: h.symbol,
      name: h.name,
      quantity: h.shares,
      costBasis: h.marketValue - h.gainLoss,
      currentPrice: h.currentPrice,
      marketValue: h.marketValue,
      currency: 'USD',
      status: 'ACTIVE' as const,
      gainLoss: h.gainLoss,
      gainLossPercent: h.gainLossPercent,
      lastUpdated: data.lastUpdated,
    })),
    lastUpdated: data.lastUpdated,
  });

  // Lookup form view
  if (isLookupMode && !portfolioData) {
    return (
      <div className="min-h-screen bg-background py-8">
        <Container size="md">
          <div className="space-y-8">
            <div className="flex items-center justify-between">
              <Link to="/">
                <Button variant="secondary" size="sm">
                  ← Back to Main Menu
                </Button>
              </Link>
            </div>
            <PageHeader
              title="Portfolio Position Inquiry"
              subtitle="Enter your account number to view portfolio details"
            />

            <main className="space-y-6 animate-slide-up">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm" role="alert">
                  {error}
                </div>
              )}

              <Card hover className="animate-fade-in max-w-lg mx-auto">
                <form onSubmit={handleLookup} className="space-y-6">
                  <div>
                    <h2 className="text-2xl font-semibold mb-4">Account Search</h2>
                    <div className="space-y-2">
                      <label htmlFor="accountNumber" className="text-sm font-medium">
                        Account Number
                      </label>
                      <input
                        id="accountNumber"
                        type="text"
                        value={accountInput}
                        onChange={(e) => { setAccountInput(e.target.value); setInputError(null); }}
                        placeholder="Enter account number"
                        maxLength={10}
                        className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                        autoFocus
                      />
                      {inputError && (
                        <p className="text-sm text-destructive" role="alert">{inputError}</p>
                      )}
                    </div>
                  </div>
                  <Button type="submit" disabled={loading} className="w-full">
                    {loading ? 'Searching...' : 'View Portfolio'}
                  </Button>
                </form>
              </Card>
            </main>
          </div>
        </Container>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-background py-8">
        <Container size="md">
          <div className="space-y-8">
            <div className="flex items-center justify-between">
              <Link to="/">
                <Button variant="secondary" size="sm">← Back to Main Menu</Button>
              </Link>
            </div>
            <PageHeader title="Portfolio Details" subtitle="Loading..." />
            <div className="space-y-4">
              <SkeletonLoader lines={3} height="h-8" />
              <SkeletonLoader lines={4} />
              <SkeletonLoader lines={2} height="h-6" />
            </div>
          </div>
        </Container>
      </div>
    );
  }

  // Error state
  if (error && !portfolioData) {
    return (
      <div className="min-h-screen bg-background py-8">
        <Container size="md">
          <div className="space-y-8">
            <div className="flex items-center justify-between">
              <Link to="/">
                <Button variant="secondary" size="sm">← Back to Main Menu</Button>
              </Link>
            </div>
            <PageHeader title="Portfolio Position Inquiry" />
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm space-y-2" role="alert">
              <p className="font-medium">Error</p>
              <p>{error}</p>
            </div>
            <div className="flex justify-center">
              <Button onClick={handleNewSearch}>Try Again</Button>
            </div>
          </div>
        </Container>
      </div>
    );
  }

  // Portfolio data view
  if (portfolioData) {
    const portfolio = toPortfolio(portfolioData);
    return (
      <div className="min-h-screen bg-background py-8">
        <Container size="md">
          <div className="space-y-8">
            <div className="flex items-center justify-between">
              <Link to="/">
                <Button variant="secondary" size="sm">← Back to Main Menu</Button>
              </Link>
            </div>
            <PageHeader
              title="Portfolio Details"
              subtitle={`Account: ${portfolioData.accountNumber}`}
            />

            <main className="space-y-6 animate-slide-up">
              <PortfolioSummaryCard portfolio={portfolio} onNewSearch={handleNewSearch} />

              <div className="space-y-4 animate-fade-in" style={{ animationDelay: '100ms' }}>
                <h3 className="text-xl font-semibold">Holdings</h3>
                <div className="grid gap-4">
                  {portfolio.positions.map((position, index) => (
                    <PositionCard
                      key={position.investmentId}
                      position={position}
                      className="animate-fade-in"
                      style={{ animationDelay: `${100 + index * 50}ms` }}
                    />
                  ))}
                </div>
              </div>

              <div className="flex justify-center gap-4 animate-fade-in" style={{ animationDelay: '200ms' }}>
                <Link to={historyPath(portfolioData.accountNumber)}>
                  <Button>View Transaction History</Button>
                </Link>
                <Button variant="outline" onClick={handleNewSearch}>
                  PF3 Exit
                </Button>
              </div>
            </main>
          </div>
        </Container>
      </div>
    );
  }

  return null;
}
