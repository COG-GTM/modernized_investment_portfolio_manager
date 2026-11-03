import { useEffect, useRef, useState } from 'react';
import Button from '../Button';
import type { EsgMetric, EsgOverrideErrors, EsgOverrideField } from '../../types/esg';
import { ApiError, overrideEsgMetric } from '../../services/api';
import { REASON_MIN_LENGTH, formatCarbonIntensity, validateEsgOverride } from '../../utils/esg';
import { trapFocus } from '../../utils/accessibility';

interface EsgOverrideDialogProps {
  isOpen: boolean;
  esg: EsgMetric;
  onClose: () => void;
  onSaved: (esg: EsgMetric) => void;
}

const inputClasses =
  'w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary';

export default function EsgOverrideDialog({ isOpen, esg, onClose, onSaved }: EsgOverrideDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const [value, setValue] = useState('');
  const [reason, setReason] = useState('');
  const [touched, setTouched] = useState<Record<EsgOverrideField, boolean>>({ value: false, reason: false });
  const [serverErrors, setServerErrors] = useState<EsgOverrideErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setValue(esg.override ? String(esg.override.value) : '');
    setReason('');
    setTouched({ value: false, reason: false });
    setServerErrors({});
    setFormError(null);
    previousFocusRef.current = document.activeElement as HTMLElement;
    const cleanup = dialogRef.current ? trapFocus(dialogRef.current) : () => {};
    return () => {
      cleanup();
      previousFocusRef.current?.focus();
    };
  }, [isOpen, esg]);

  useEffect(() => {
    if (!isOpen) return;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !submitting) {
        e.preventDefault();
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose, submitting]);

  if (!isOpen) return null;

  const clientErrors = validateEsgOverride(value, reason);
  const isValid = Object.keys(clientErrors).length === 0;
  const errorFor = (field: EsgOverrideField) => serverErrors[field] ?? (touched[field] ? clientErrors[field] : undefined);
  const valueError = errorFor('value');
  const reasonError = errorFor('reason');

  const handleChange = (field: EsgOverrideField, next: string) => {
    if (field === 'value') setValue(next);
    else setReason(next);
    setTouched((t) => ({ ...t, [field]: true }));
    setServerErrors((errors) => ({ ...errors, [field]: undefined }));
    setFormError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched({ value: true, reason: true });
    if (!isValid || submitting) return;

    setSubmitting(true);
    setFormError(null);
    try {
      const updated = await overrideEsgMetric(esg.accountNumber, { value: Number(value), reason: reason.trim() });
      onSaved(updated);
    } catch (err) {
      if (err instanceof ApiError) {
        setServerErrors(err.fieldErrors);
        setFormError(err.message);
      } else {
        setFormError('An unexpected error occurred. Please try again.');
      }
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
      aria-describedby="esg-override-description"
    >
      <div ref={dialogRef} className="w-full max-w-md mx-4 rounded-lg border bg-card p-6 shadow-lg">
        <h2 id="esg-override-title" className="text-lg font-semibold">
          Override carbon intensity
        </h2>
        <p id="esg-override-description" className="mt-1 text-sm text-muted-foreground">
          Applies to {esg.portfolioId} for the current as-of month ({esg.asOfMonth}) only. Computed value:{' '}
          {formatCarbonIntensity(esg.computedValue)} {esg.unit}.
        </p>

        <form onSubmit={handleSubmit} noValidate className="mt-4 space-y-4">
          {formError && (
            <div role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {formError}
            </div>
          )}

          <div className="space-y-1">
            <label htmlFor="esg-override-value" className="block text-sm font-medium">
              Override value ({esg.unit})
            </label>
            <input
              id="esg-override-value"
              type="number"
              inputMode="decimal"
              min={0}
              step="any"
              value={value}
              onChange={(e) => handleChange('value', e.target.value)}
              onBlur={() => setTouched((t) => ({ ...t, value: true }))}
              aria-invalid={valueError ? true : undefined}
              aria-describedby={valueError ? 'esg-override-value-error' : undefined}
              className={`${inputClasses} ${valueError ? 'border-red-500' : 'border-border'}`}
            />
            {valueError && (
              <p id="esg-override-value-error" className="text-sm text-red-600">
                {valueError}
              </p>
            )}
          </div>

          <div className="space-y-1">
            <label htmlFor="esg-override-reason" className="block text-sm font-medium">
              Reason
            </label>
            <textarea
              id="esg-override-reason"
              rows={3}
              value={reason}
              onChange={(e) => handleChange('reason', e.target.value)}
              onBlur={() => setTouched((t) => ({ ...t, reason: true }))}
              aria-invalid={reasonError ? true : undefined}
              aria-describedby={`esg-override-reason-hint${reasonError ? ' esg-override-reason-error' : ''}`}
              className={`${inputClasses} ${reasonError ? 'border-red-500' : 'border-border'}`}
            />
            <p id="esg-override-reason-hint" className="text-xs text-muted-foreground">
              Required, at least {REASON_MIN_LENGTH} characters ({reason.trim().length}/{REASON_MIN_LENGTH}).
            </p>
            {reasonError && (
              <p id="esg-override-reason-error" className="text-sm text-red-600">
                {reasonError}
              </p>
            )}
          </div>

          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={!isValid || submitting}>
              {submitting ? 'Saving…' : 'Save override'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
