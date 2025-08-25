import { Link } from 'react-router-dom';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button } from '../components';

export default function SystemAdministration() {
  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="md">
        <div className="space-y-8">
          <PageHeader 
            title="System Administration"
            subtitle="Manage user accounts, permissions, and system settings"
            className="mb-8"
          />
          
          <Card className="p-8 text-center animate-fade-in">
            <div className="space-y-6">
              <div className="w-16 h-16 mx-auto bg-primary/10 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              
              <h2 className="text-2xl font-semibold text-foreground">
                System Administration Panel
              </h2>
              
              <p className="text-muted-foreground max-w-md mx-auto">
                Manage user accounts, configure system permissions, and adjust application settings. 
                Administrative functions for system maintenance and user management.
              </p>
              
              <div className="pt-4">
                <p className="text-sm text-muted-foreground mb-4">
                  Coming Soon: User management, role-based access control, and system configuration tools.
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
