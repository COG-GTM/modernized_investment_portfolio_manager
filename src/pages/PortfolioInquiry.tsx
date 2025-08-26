import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button, PositionCard, PortfolioSummary, Alert } from '../components';
import { AccountInput } from '../components/AccountInput';
import { accountFormSchema, type AccountFormData, type PortfolioSummary as PortfolioSummaryType } from '../types/account';
import { fetchPortfolio, ApiError } from '../services/api';

export default function PortfolioInquiry() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [portfolioData, setPortfolioData] = useState<PortfolioSummaryType | null>(null);
  const [error, setError] = useState<string | null>(null);

  const methods = useForm<AccountFormData>({
    resolver: zodResolver(accountFormSchema),
    mode: 'onChange',
  });

  const { handleSubmit, formState: { isValid } } = methods;

  const onSubmit = async (data: AccountFormData) => {
    setIsSubmitting(true);
    setError(null);
    
    try {
      const portfolio = await fetchPortfolio(data.accountNumber);
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
    methods.reset();
  };

  if (portfolioData) {
    return (
      <div className="min-h-screen bg-background py-8">
        <Container size="md">
          <div className="space-y-8">
            <PageHeader 
              title="Portfolio Details"
              subtitle={`Account: ${portfolioData.accountNumber}`}
            />
            
            <main className="space-y-6 animate-slide-up">
              <PortfolioSummary 
                portfolio={{
                  portfolioId: `PF-${portfolioData.accountNumber}`,
                  accountNumber: portfolioData.accountNumber,
                  totalValue: portfolioData.totalValue,
                  totalCostBasis: portfolioData.totalValue - portfolioData.totalGainLoss,
                  totalGainLoss: portfolioData.totalGainLoss,
                  totalGainLossPercent: portfolioData.totalGainLossPercent,
                  currency: 'USD',
                  positions: portfolioData.holdings.map((holding: any) => ({
                    portfolioId: `PF-${portfolioData.accountNumber}`,
                    investmentId: `INV-${holding.symbol}-001`,
                    symbol: holding.symbol,
                    name: holding.name,
                    quantity: holding.shares,
                    costBasis: holding.marketValue - holding.gainLoss,
                    currentPrice: holding.currentPrice,
                    marketValue: holding.marketValue,
                    currency: 'USD',
                    status: 'ACTIVE' as const,
                    gainLoss: holding.gainLoss,
                    gainLossPercent: holding.gainLossPercent,
                    lastUpdated: portfolioData.lastUpdated,
                  })),
                  lastUpdated: portfolioData.lastUpdated,
                }}
                onNewSearch={resetForm}
              />

              <div className="space-y-4 animate-fade-in" style={{ animationDelay: '100ms' }}>
                <h3 className="text-xl font-semibold">Holdings</h3>
                <div className="grid gap-4">
                  {portfolioData.holdings.map((holding: any, index: number) => (
                    <PositionCard
                      key={holding.symbol}
                      position={{
                        portfolioId: `PF-${portfolioData.accountNumber}`,
                        investmentId: `INV-${holding.symbol}-001`,
                        symbol: holding.symbol,
                        name: holding.name,
                        quantity: holding.shares,
                        costBasis: holding.marketValue - holding.gainLoss,
                        currentPrice: holding.currentPrice,
                        marketValue: holding.marketValue,
                        currency: 'USD',
                        status: 'ACTIVE' as const,
                        gainLoss: holding.gainLoss,
                        gainLossPercent: holding.gainLossPercent,
                        lastUpdated: portfolioData.lastUpdated,
                      }}
                      className="animate-fade-in"
                      style={{ animationDelay: `${100 + (index * 50)}ms` }}
                    />
                  ))}
                </div>
              </div>
              
              <div className="flex gap-4 justify-center animate-fade-in" style={{ animationDelay: '200ms' }}>
                <Link to={ROUTES.MAIN_MENU}>
                  <Button variant="secondary">
                    Back to Main Menu
                  </Button>
                </Link>
                <Link to={`${ROUTES.TRANSACTION_HISTORY}?account=${portfolioData.accountNumber}`}>
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
          <PageHeader 
            title="Portfolio Inquiry"
            subtitle="Enter your account number to view portfolio details"
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
            
            <div className="flex gap-4 justify-center animate-fade-in" style={{ animationDelay: '200ms' }}>
              <Link to={ROUTES.MAIN_MENU}>
                <Button variant="secondary">
                  Back to Main Menu
                </Button>
              </Link>
            </div>
          </main>
        </div>
      </Container>
    </div>
  );
}
