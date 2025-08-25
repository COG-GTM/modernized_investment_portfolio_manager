import { Link } from 'react-router-dom';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button } from '../components';

export default function ReportsAnalytics() {
  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="md">
        <div className="space-y-8">
          <PageHeader 
            title="Reports & Analytics"
            subtitle="Business intelligence reports and portfolio analytics"
            className="mb-8"
          />
          
          <Card className="p-8 text-center animate-fade-in">
            <div className="space-y-6">
              <div className="w-16 h-16 mx-auto bg-primary/10 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              
              <h2 className="text-2xl font-semibold text-foreground">
                Reports & Analytics Dashboard
              </h2>
              
              <p className="text-muted-foreground max-w-md mx-auto">
                Access comprehensive business intelligence reports, portfolio performance analytics, 
                and investment insights. This feature will provide detailed analysis of your investment data.
              </p>
              
              <div className="pt-4">
                <p className="text-sm text-muted-foreground mb-4">
                  Coming Soon: Portfolio performance charts, risk analysis, and custom reporting tools.
                </p>
              </div>
            </div>
          </Card>
          
          <div className="flex gap-4 justify-center animate-fade-in" style={{ animationDelay: '200ms' }}>
            <Link to={ROUTES.MAIN_MENU}>
              <Button variant="secondary">
                Back to Main Menu
              </Button>
            </Link>
          </div>
        </div>
      </Container>
    </div>
  );
}
