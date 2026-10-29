import { formatNumber } from './format';

export function formatAsOfMonth(asOfMonth: string): string {
  const match = /^(\d{4})-(\d{2})$/.exec(asOfMonth);
  if (!match) return asOfMonth;
  const date = new Date(Number(match[1]), Number(match[2]) - 1, 1);
  return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
}

export function formatIntensity(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return 'n/a';
  return formatNumber(value, 2);
}

export function formatCoverage(value: number): string {
  return `${formatNumber(value, 1)}%`;
}

export function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
