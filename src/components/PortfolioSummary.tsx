import Card from './Card';
import { Portfolio } from '../types';
import { formatCurrency, formatPercentage, formatLastUpdated, getGainLossColorClass } from '../utils/format';

interface PortfolioSummaryProps {
  portfolio: Portfolio;
  onNewSearch?: () => void;
  className?: string;
}

export default function PortfolioSummary({ portfolio, onNewSearch, className = '' }: PortfolioSummaryProps) {
  const gainLossColorClass = getGainLossColorClass(portfolio.totalGainLoss);

  return (
    <Card hover className={`animate-fade-in ${className}`}>
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-semibold">Portfolio Summary</h2>
            <p className="text-sm text-muted-foreground">
              Last updated: {formatLastUpdated(portfolio.lastUpdated)}
            </p>
          </div>
          {onNewSearch && (
            <button
              onClick={onNewSearch}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              New Search
            </button>
          )}
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-primary/5 rounded-lg p-4">
            <p className="text-sm text-muted-foreground">Total Value</p>
            <p className="text-2xl font-bold">
              {formatCurrency(portfolio.totalValue, portfolio.currency)}
            </p>
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <p className="text-sm text-muted-foreground">Total Gain/Loss</p>
            <p className={`text-2xl font-bold ${gainLossColorClass}`}>
              {formatCurrency(portfolio.totalGainLoss, portfolio.currency)}
            </p>
          </div>
          <div className="bg-blue-50 rounded-lg p-4">
            <p className="text-sm text-muted-foreground">Gain/Loss %</p>
            <p className={`text-2xl font-bold ${gainLossColorClass}`}>
              {formatPercentage(portfolio.totalGainLossPercent)}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
          <div>
            <p className="text-sm text-muted-foreground">Portfolio ID</p>
            <p className="font-medium">{portfolio.portfolioId}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Account</p>
            <p className="font-medium">{portfolio.accountNumber}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Total Cost Basis</p>
            <p className="font-medium">{formatCurrency(portfolio.totalCostBasis, portfolio.currency)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Positions</p>
            <p className="font-medium">{portfolio.positions.length}</p>
          </div>
        </div>
      </div>
    </Card>
  );
}
