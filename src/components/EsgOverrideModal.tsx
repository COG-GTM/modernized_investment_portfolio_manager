import { useEffect, useRef, useState } from 'react';
import { trapFocus } from '../utils/accessibility';
import { ESG_MIN_REASON_LENGTH, type EsgMetric } from '../types/esg';
import { formatAsOfMonth, formatIntensity } from '../utils/esgFormat';

export type OverrideMode = 'override' | 'clear';

export interface EsgOverrideModalProps {
  isOpen: boolean;
  mode: OverrideMode;
  metric: EsgMetric | null;
  onSubmit: (payload: { value: number | null; reason: string }) => Promise<void>;
  onCancel: () => void;
  serverError?: string | null;
}

export function validateOverrideForm(mode: OverrideMode, rawValue: string, reason: string): { value?: string; reason?: string } {
  const errors: { value?: string; reason?: string } = {};
  if (mode === 'override') {
    if (rawValue.trim() === '') {
      errors.value = 'Value is required';
    } else {
      const numeric = Number(rawValue);
      if (!Number.isFinite(numeric)) {
        errors.value = 'Value must be a number';
      } else if (numeric < 0) {
        errors.value = 'Value must be zero or greater';
      }
    }
  }
  if (reason.trim().length < ESG_MIN_REASON_LENGTH) {
    errors.reason = `Reason is mandatory and must be at least ${ESG_MIN_REASON_LENGTH} characters`;
  }
  return errors;
}

export default function EsgOverrideModal({ isOpen, mode, metric, onSubmit, onCancel, serverError = null }: EsgOverrideModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const [rawValue, setRawValue] = useState('');
  const [reason, setReason] = useState('');
  const [errors, setErrors] = useState<{ value?: string; reason?: string }>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setRawValue(metric?.override?.value !== undefined && metric?.override ? String(metric.override.value) : '');
      setReason('');
      setErrors({});
      setSubmitting(false);
      return dialogRef.current ? trapFocus(dialogRef.current) : undefined;
    }
  }, [isOpen, metric]);

  useEffect(() => {
    if (!isOpen) return;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onCancel();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  const title = mode === 'override' ? 'Override carbon intensity' : 'Clear carbon intensity override';
  const asOf = metric ? formatAsOfMonth(metric.as_of_month) : '';

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const validation = validateOverrideForm(mode, rawValue, reason);
    setErrors(validation);
    if (Object.keys(validation).length > 0) return;
    setSubmitting(true);
    try {
      await onSubmit({ value: mode === 'override' ? Number(rawValue) : null, reason: reason.trim() });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="esg-override-title"
    >
      <div ref={dialogRef} className="w-full max-w-[28rem] mx-4 rounded-xl border bg-card p-6 shadow-lg">
        <h2 id="esg-override-title" className="text-lg font-semibold">{title}</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Applies to the current as-of month ({asOf}). Computed value: {formatIntensity(metric?.computed_value)} {metric?.unit}.
        </p>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4" noValidate>
          {mode === 'override' && (
            <div>
              <label htmlFor="esg-override-value" className="block text-sm font-medium">
                Override value ({metric?.unit ?? 'tCO2e per $M revenue'})
              </label>
              <input
                id="esg-override-value"
                type="number"
                step="any"
                min="0"
                inputMode="decimal"
                value={rawValue}
                onChange={(e) => setRawValue(e.target.value)}
                aria-invalid={Boolean(errors.value)}
                aria-describedby={errors.value ? 'esg-override-value-error' : undefined}
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors.value && (
                <p id="esg-override-value-error" className="mt-1 text-sm text-red-600" role="alert">{errors.value}</p>
              )}
            </div>
          )}

          <div>
            <label htmlFor="esg-override-reason" className="block text-sm font-medium">
              Reason (minimum {ESG_MIN_REASON_LENGTH} characters)
            </label>
            <textarea
              id="esg-override-reason"
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              aria-invalid={Boolean(errors.reason)}
              aria-describedby={errors.reason ? 'esg-override-reason-error' : undefined}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.reason && (
              <p id="esg-override-reason-error" className="mt-1 text-sm text-red-600" role="alert">{errors.reason}</p>
            )}
          </div>

          {serverError && (
            <p className="text-sm text-red-600" role="alert" data-testid="esg-server-error">{serverError}</p>
          )}

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium rounded-md border border-gray-300 bg-white hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 text-sm font-medium rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {submitting ? 'Saving...' : mode === 'override' ? 'Save override' : 'Clear override'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
