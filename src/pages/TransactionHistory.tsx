import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button, SkeletonLoader } from '../components';

export default function TransactionHistory() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 1200);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="md">
        <div className="space-y-8">
          <PageHeader 
            title="Transaction History"
            subtitle="Review your investment transaction activity"
          />
          
          <main className="space-y-6 animate-slide-up">
            <Card hover className="animate-fade-in">
              <h2 className="text-2xl font-semibold mb-4">Recent Transactions</h2>
              {loading ? (
                <div className="space-y-4">
                  <SkeletonLoader lines={3} />
                  <SkeletonLoader lines={1} height="h-2" />
                </div>
              ) : (
                <>
                  <p className="text-muted-foreground mb-4">
                    This page will display a comprehensive list of all investment transactions 
                    including purchases, sales, dividends, and other portfolio activities.
                  </p>
                  <div className="text-sm text-muted-foreground space-y-2">
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
                </>
              )}
            </Card>
            
            <div className="flex gap-4 justify-center animate-fade-in" style={{ animationDelay: '200ms' }}>
              <Link to={ROUTES.MAIN_MENU}>
                <Button variant="secondary">
                  Back to Main Menu
                </Button>
              </Link>
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
