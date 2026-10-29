import type { EsgMetric } from '../types/esg';
import { formatAsOfMonth, formatCoverage, formatIntensity, formatTimestamp } from '../utils/esgFormat';

export interface CarbonIntensityCardProps {
  metric: EsgMetric | null;
  loading?: boolean;
  error?: string | null;
  onOverride?: () => void;
  onClearOverride?: () => void;
  onViewHistory?: () => void;
  className?: string;
}

const actionButtonClass =
  'px-3 py-1.5 text-sm font-medium rounded-md border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50';

export default function CarbonIntensityCard({
  metric,
  loading = false,
  error = null,
  onOverride,
  onClearOverride,
  onViewHistory,
  className = '',
}: CarbonIntensityCardProps) {
  const isOverride = metric?.source === 'override';

  return (
    <section
      aria-labelledby="carbon-intensity-title"
      data-testid="carbon-intensity-card"
      className={`rounded-lg border border-border p-4 ${isOverride ? 'bg-amber-50 border-amber-200' : 'bg-emerald-50'} ${className}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 id="carbon-intensity-title" className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
            Carbon Intensity (WACI)
          </h3>
          {metric && (
            <p className="text-xs text-muted-foreground">As of {formatAsOfMonth(metric.as_of_month)}</p>
          )}
        </div>
        {metric && isOverride && (
          <span
            data-testid="override-indicator"
            className="inline-flex items-center rounded-full bg-amber-200 px-2.5 py-0.5 text-xs font-semibold text-amber-900"
            title={metric.override?.reason}
          >
            Override
          </span>
        )}
      </div>

      {loading && (
        <p className="mt-3 text-sm text-muted-foreground" role="status">Loading carbon intensity...</p>
      )}

      {!loading && error && (
        <p className="mt-3 text-sm text-red-600" role="alert">{error}</p>
      )}

      {!loading && !error && !metric && (
        <div className="mt-3" data-testid="carbon-intensity-empty">
          <p className="text-2xl font-bold text-gray-400">Not available</p>
          <p className="text-sm text-muted-foreground">
            No emissions data has been loaded for this portfolio yet. The metric appears after the monthly ESG feed is processed.
          </p>
        </div>
      )}

      {!loading && !error && metric && (
        <div className="mt-3 space-y-3">
          <div>
            <p className="text-2xl font-bold" data-testid="carbon-intensity-value">
              {formatIntensity(metric.effective_value)}{' '}
              <span className="text-sm font-normal text-muted-foreground">{metric.unit}</span>
            </p>
            {isOverride && metric.override && (
              <p className="text-xs text-amber-900 mt-1" data-testid="override-detail">
                Overrides computed value {formatIntensity(metric.computed_value)} by {metric.override.changed_by} on{' '}
                {formatTimestamp(metric.override.changed_at)}: {metric.override.reason}
              </p>
            )}
          </div>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-muted-foreground">Coverage</dt>
              <dd className="font-medium" data-testid="carbon-intensity-coverage">{formatCoverage(metric.coverage_pct)} of market value</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Source</dt>
              <dd className="font-medium capitalize">{metric.source}</dd>
            </div>
          </dl>
          <div className="flex flex-wrap gap-2 pt-1">
            {onOverride && (
              <button type="button" className={actionButtonClass} onClick={onOverride}>
                {isOverride ? 'Change override' : 'Override value'}
              </button>
            )}
            {isOverride && onClearOverride && (
              <button type="button" className={actionButtonClass} onClick={onClearOverride}>
                Clear override
              </button>
            )}
            {onViewHistory && (
              <button type="button" className={actionButtonClass} onClick={onViewHistory}>
                View history
              </button>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
