import Button from '../Button';
import type { EsgMetric } from '../../types/esg';
import { formatCarbonIntensity } from '../../utils/esg';

interface CarbonIntensityTileProps {
  esg: EsgMetric | null;
  loading?: boolean;
  error?: string | null;
  onOverrideClick?: () => void;
}

export default function CarbonIntensityTile({ esg, loading = false, error = null, onOverrideClick }: CarbonIntensityTileProps) {
  const isOverridden = esg?.source === 'override' && esg.override !== null;

  return (
    <section
      aria-labelledby="carbon-intensity-heading"
      className={`rounded-lg p-4 border ${isOverridden ? 'bg-amber-50 border-amber-300' : 'bg-emerald-50 border-transparent'}`}
      data-testid="carbon-intensity-tile"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h3 id="carbon-intensity-heading" className="text-sm text-muted-foreground">
              Carbon intensity (WACI)
            </h3>
            {isOverridden && (
              <span
                className="inline-flex items-center rounded-full bg-amber-200 px-2 py-0.5 text-xs font-semibold text-amber-900"
                data-testid="esg-override-indicator"
                title={esg?.override?.reason}
              >
                Overridden
              </span>
            )}
          </div>

          {loading && <p className="text-sm text-muted-foreground">Loading carbon intensity…</p>}

          {!loading && error && <p className="text-sm text-red-600">{error}</p>}

          {!loading && !error && esg && !esg.hasMetric && (
            <p className="text-sm text-muted-foreground">No carbon intensity data for this portfolio yet.</p>
          )}

          {!loading && !error && esg?.hasMetric && (
            <>
              <p className="text-2xl font-bold" aria-live="polite" data-testid="esg-effective-value">
                {formatCarbonIntensity(esg.effectiveValue)}{' '}
                <span className="text-sm font-normal text-muted-foreground">{esg.unit}</span>
              </p>
              <p className="text-xs text-muted-foreground">
                As of {esg.asOfMonth} · Coverage {esg.coveragePct?.toFixed(2)}%
              </p>
            </>
          )}
        </div>

        {!loading && !error && esg?.hasMetric && onOverrideClick && (
          <Button variant="outline" size="sm" aria-haspopup="dialog" onClick={onOverrideClick}>
            {isOverridden ? 'Change override' : 'Override value'}
          </Button>
        )}
      </div>

      {isOverridden && esg?.override && (
        <div className="mt-3 border-t border-amber-200 pt-3 text-sm space-y-1" data-testid="esg-override-details">
          <p>
            <span className="text-muted-foreground">Computed value:</span>{' '}
            {formatCarbonIntensity(esg.computedValue)}
          </p>
          <p>
            <span className="text-muted-foreground">Reason:</span> {esg.override.reason}
          </p>
          <p className="text-xs text-muted-foreground">
            Overridden by {esg.override.overriddenBy} on {new Date(esg.override.overriddenAt).toLocaleString()}
          </p>
        </div>
      )}
    </section>
  );
}
