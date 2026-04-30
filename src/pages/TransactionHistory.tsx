import { Link, useSearchParams } from 'react-router-dom';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button, SkeletonLoader, Alert } from '../components';
import { useTransactionsQuery } from '../hooks/usePortfolioQuery';

export default function TransactionHistory() {
  const [searchParams] = useSearchParams();
  const accountNumber = searchParams.get('account');

  const { data: transactionData, error: queryError, isLoading } = useTransactionsQuery(accountNumber);

  const error = queryError ? (queryError as Error).message : null;

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
            title="Transaction History"
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
                {transactionData ? `Transactions for Account ${transactionData.accountNumber}` : 'Recent Transactions'}
              </h2>
              {isLoading ? (
                <div className="space-y-4">
                  <SkeletonLoader lines={3} />
                  <SkeletonLoader lines={1} height="h-2" />
                </div>
              ) : transactionData ? (
                <>
                  <p className="text-muted-foreground mb-4">
                    {transactionData.message}
                  </p>
                  {transactionData.transactions.length === 0 ? (
                    <div className="text-sm text-muted-foreground space-y-2">
                      <p>No transactions found for this account.</p>
                      <div className="mt-4 space-y-2">
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-primary rounded-full"></div>
                          <span>Buy/sell transactions</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-primary rounded-full"></div>
                          <span>Dividend payments</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-primary rounded-full"></div>
                          <span>Fee and commission details</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-primary rounded-full"></div>
                          <span>Transaction filtering and search</span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {transactionData.transactions.map((transaction, index) => (
                        <div key={index} className="p-3 border rounded-lg">
                          <pre className="text-sm">{JSON.stringify(transaction, null, 2)}</pre>
                        </div>
                      ))}
                    </div>
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
          </main>
        </div>
      </Container>
    </div>
  );
}
