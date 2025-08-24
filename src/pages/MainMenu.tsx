import { Link } from 'react-router-dom';
import { ROUTES } from '../types/routes';

export default function MainMenu() {
  return (
    <div className="p-8 font-sans min-h-screen bg-background">
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-primary">
            Investment Portfolio Manager
          </h1>
          <p className="text-lg text-muted-foreground">
            Main Menu - Select an option below
          </p>
        </header>
        
        <main className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 max-w-2xl mx-auto">
            <Link 
              to={ROUTES.PORTFOLIO_INQUIRY}
              className="block p-6 bg-card border border-border rounded-lg hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              <h2 className="text-xl font-semibold mb-2">Portfolio Inquiry</h2>
              <p className="text-muted-foreground">
                View and analyze your investment portfolio holdings and performance
              </p>
            </Link>
            
            <Link 
              to={ROUTES.TRANSACTION_HISTORY}
              className="block p-6 bg-card border border-border rounded-lg hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              <h2 className="text-xl font-semibold mb-2">Transaction History</h2>
              <p className="text-muted-foreground">
                Review your investment transaction history and activity
              </p>
            </Link>
          </div>
        </main>
      </div>
    </div>
  );
}
