import { Link } from 'react-router-dom';
import { ROUTES } from '../types/routes';

export default function PortfolioInquiry() {
  return (
    <div className="p-8 font-sans min-h-screen bg-background">
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-primary">
            Portfolio Inquiry
          </h1>
          <p className="text-lg text-muted-foreground">
            View and analyze your investment portfolio
          </p>
        </header>
        
        <main className="space-y-6">
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Portfolio Overview</h2>
            <p className="text-muted-foreground mb-4">
              This page will display detailed portfolio information including holdings, 
              performance metrics, and asset allocation charts.
            </p>
            <div className="text-sm text-muted-foreground">
              <p>• Current portfolio value</p>
              <p>• Asset allocation breakdown</p>
              <p>• Performance analytics</p>
              <p>• Individual holding details</p>
            </div>
          </div>
          
          <div className="flex gap-4 justify-center">
            <Link 
              to={ROUTES.MAIN_MENU}
              className="px-6 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
            >
              Back to Main Menu
            </Link>
            <Link 
              to={ROUTES.TRANSACTION_HISTORY}
              className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            >
              View Transaction History
            </Link>
          </div>
        </main>
      </div>
    </div>
  );
}
