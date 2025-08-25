import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button } from '../components';
import { AccountInput } from '../components/AccountInput';
import { accountFormSchema, type AccountFormData, type PortfolioSummary } from '../types/account';
import { generateMockPortfolio } from '../utils/mockData';

export default function PortfolioInquiry() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [portfolioData, setPortfolioData] = useState<PortfolioSummary | null>(null);

  const methods = useForm<AccountFormData>({
    resolver: zodResolver(accountFormSchema),
    mode: 'onChange',
  });

  const { handleSubmit, formState: { isValid } } = methods;

  const onSubmit = async (data: AccountFormData) => {
    setIsSubmitting(true);
    
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const mockPortfolio = generateMockPortfolio(data.accountNumber);
    setPortfolioData(mockPortfolio);
    setIsSubmitting(false);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && isValid && !isSubmitting) {
      handleSubmit(onSubmit)();
    }
  };

  const resetForm = () => {
    setPortfolioData(null);
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
              <Card hover className="animate-fade-in">
                <div className="space-y-6">
                  <div className="flex justify-between items-start">
                    <div>
                      <h2 className="text-2xl font-semibold">Portfolio Summary</h2>
                      <p className="text-sm text-muted-foreground">
                        Last updated: {portfolioData.lastUpdated}
                      </p>
                    </div>
                    <Button onClick={resetForm} variant="outline">
                      New Search
                    </Button>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-primary/5 rounded-lg p-4">
                      <p className="text-sm text-muted-foreground">Total Value</p>
                      <p className="text-2xl font-bold">
                        ${portfolioData.totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4">
                      <p className="text-sm text-muted-foreground">Total Gain/Loss</p>
                      <p className={`text-2xl font-bold ${portfolioData.totalGainLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        ${portfolioData.totalGainLoss.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </p>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-4">
                      <p className="text-sm text-muted-foreground">Gain/Loss %</p>
                      <p className={`text-2xl font-bold ${portfolioData.totalGainLossPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {portfolioData.totalGainLossPercent.toFixed(2)}%
                      </p>
                    </div>
                  </div>
                </div>
              </Card>

              <Card className="animate-fade-in" style={{ animationDelay: '100ms' }}>
                <h3 className="text-xl font-semibold mb-4">Holdings</h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2">Symbol</th>
                        <th className="text-left py-2">Name</th>
                        <th className="text-right py-2">Shares</th>
                        <th className="text-right py-2">Price</th>
                        <th className="text-right py-2">Market Value</th>
                        <th className="text-right py-2">Gain/Loss</th>
                      </tr>
                    </thead>
                    <tbody>
                      {portfolioData.holdings.map((holding) => (
                        <tr key={holding.symbol} className="border-b">
                          <td className="py-3 font-medium">{holding.symbol}</td>
                          <td className="py-3 text-muted-foreground">{holding.name}</td>
                          <td className="py-3 text-right">{holding.shares.toLocaleString()}</td>
                          <td className="py-3 text-right">${holding.currentPrice.toFixed(2)}</td>
                          <td className="py-3 text-right">${holding.marketValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                          <td className={`py-3 text-right ${holding.gainLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            ${holding.gainLoss.toLocaleString('en-US', { minimumFractionDigits: 2 })} ({holding.gainLossPercent.toFixed(2)}%)
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
              
              <div className="flex gap-4 justify-center animate-fade-in" style={{ animationDelay: '200ms' }}>
                <Link to={ROUTES.MAIN_MENU}>
                  <Button variant="secondary">
                    Back to Main Menu
                  </Button>
                </Link>
                <Link to={ROUTES.TRANSACTION_HISTORY}>
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
