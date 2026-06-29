import Card from './Card';
import LoadingSpinner from './LoadingSpinner';
import { Alert } from './ui/alert';
import { useDiversification } from '../hooks/useDiversification';
import { formatCurrency, formatPercentage } from '../utils/format';

interface SectorDiversificationProps {
  accountNumber: string;
  currency?: string;
  className?: string;
  style?: React.CSSProperties;
}

export default function SectorDiversification({
  accountNumber,
  currency = 'USD',
  className = '',
  style,
}: SectorDiversificationProps) {
  const { data, isLoading, error } = useDiversification(accountNumber);

  return (
    <Card hover className={`animate-fade-in ${className}`} style={style}>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-semibold">Sector Diversification</h2>
          <p className="text-sm text-muted-foreground">
            Allocation of holdings across market sectors
          </p>
        </div>

        {isLoading && (
          <div className="flex justify-center py-6">
            <LoadingSpinner size="md" />
          </div>
        )}

        {error && !isLoading && (
          <Alert variant="destructive">{error}</Alert>
        )}

        {data && !isLoading && !error && (
          <div className="space-y-4">
            {data.sectors.map((sector) => (
              <div key={sector.sector} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{sector.sector}</span>
                  <span className="text-muted-foreground">
                    {formatCurrency(sector.marketValue, currency)} ·{' '}
                    {sector.holdingsCount} {sector.holdingsCount === 1 ? 'holding' : 'holdings'}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary transition-smooth"
                      style={{ width: `${sector.allocationPercent}%` }}
                    />
                  </div>
                  <span className="w-16 text-right text-sm font-semibold">
                    {formatPercentage(sector.allocationPercent)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}
