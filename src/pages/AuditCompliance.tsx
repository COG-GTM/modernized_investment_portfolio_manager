import { Link } from 'react-router-dom';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button } from '../components';

export default function AuditCompliance() {
  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="md">
        <div className="space-y-8">
          <PageHeader 
            title="Audit & Compliance"
            subtitle="Security logs, compliance reports, and audit trails"
            className="mb-8"
          />
          
          <Card className="p-8 text-center animate-fade-in">
            <div className="space-y-6">
              <div className="w-16 h-16 mx-auto bg-primary/10 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              
              <h2 className="text-2xl font-semibold text-foreground">
                Audit & Compliance Center
              </h2>
              
              <p className="text-muted-foreground max-w-md mx-auto">
                Monitor security events, generate compliance reports, and review audit trails. 
                Ensure regulatory compliance and maintain security oversight.
              </p>
              
              <div className="pt-4">
                <p className="text-sm text-muted-foreground mb-4">
                  Coming Soon: Security logs, compliance dashboards, and audit trail reporting.
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
