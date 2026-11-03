import type { EsgOverrideErrors } from '../types/esg';

export const REASON_MIN_LENGTH = 10;
export const REASON_MAX_LENGTH = 1000;

// Count code points, not UTF-16 units, to match the server's len(str.strip()).
export function reasonLength(reason: string): number {
  return Array.from(reason.trim()).length;
}

export function validateEsgOverride(value: string, reason: string): EsgOverrideErrors {
  const errors: EsgOverrideErrors = {};

  if (value.trim() === '') {
    errors.value = 'Value is required';
  } else {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) {
      errors.value = 'Value must be a number';
    } else if (parsed < 0) {
      errors.value = 'Value must be non-negative';
    }
  }

  const trimmedLength = reasonLength(reason);
  if (trimmedLength < REASON_MIN_LENGTH) {
    errors.reason = `Reason must be at least ${REASON_MIN_LENGTH} characters`;
  } else if (trimmedLength > REASON_MAX_LENGTH) {
    errors.reason = `Reason must be at most ${REASON_MAX_LENGTH} characters`;
  }

  return errors;
}

export function formatCarbonIntensity(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
