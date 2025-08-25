import { Link } from 'react-router-dom';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button } from '../components';

export default function HelpDocumentation() {
  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="md">
        <div className="space-y-8">
          <PageHeader 
            title="Help & Documentation"
            subtitle="User guides, documentation, and support resources"
            className="mb-8"
          />
          
          <Card className="p-8 text-center animate-fade-in">
            <div className="space-y-6">
              <div className="w-16 h-16 mx-auto bg-primary/10 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              
              <h2 className="text-2xl font-semibold text-foreground">
                Help & Support Center
              </h2>
              
              <p className="text-muted-foreground max-w-md mx-auto">
                Access comprehensive user guides, system documentation, and support resources. 
                Get help with using the Investment Portfolio Management System.
              </p>
              
              <div className="pt-4">
                <p className="text-sm text-muted-foreground mb-4">
                  Coming Soon: User manuals, FAQ section, video tutorials, and contact support.
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
