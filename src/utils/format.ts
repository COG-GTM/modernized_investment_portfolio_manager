export function formatCurrency(
  value: number,
  currency: string = 'USD',
  options: Intl.NumberFormatOptions = {}
): string {
  const defaultOptions: Intl.NumberFormatOptions = {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
    ...options,
  };

  return new Intl.NumberFormat('en-US', defaultOptions).format(value);
}

export function formatNumber(
  value: number,
  decimals: number = 2,
  options: Intl.NumberFormatOptions = {}
): string {
  const defaultOptions: Intl.NumberFormatOptions = {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
    ...options,
  };

  return new Intl.NumberFormat('en-US', defaultOptions).format(value);
}

export function formatPercentage(
  value: number,
  decimals: number = 2
): string {
  return `${formatNumber(value, decimals)}%`;
}

export function formatLastUpdated(date: Date | string): string {
  let dateObj: Date;
  
  if (typeof date === 'string') {
    dateObj = new Date(date);
    if (isNaN(dateObj.getTime())) {
      dateObj = new Date();
    }
  } else {
    dateObj = date;
  }
  
  return dateObj.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function getGainLossColorClass(value: number): string {
  if (value > 0) return 'text-green-600';
  if (value < 0) return 'text-red-600';
  return 'text-gray-600';
}

export function formatGainLoss(
  value: number,
  percentage: number,
  currency: string = 'USD'
): {
  formatted: string;
  colorClass: string;
} {
  const sign = value >= 0 ? '+' : '';
  const formatted = `${sign}${formatCurrency(value, currency)} (${sign}${formatPercentage(percentage)})`;
  const colorClass = getGainLossColorClass(value);
  
  return { formatted, colorClass };
}
