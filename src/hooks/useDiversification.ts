import { useEffect, useState } from 'react';
import type { DiversificationSummary } from '../types/account';
import { fetchPortfolioDiversification, ApiError } from '../services/api';

interface UseDiversificationResult {
  data: DiversificationSummary | null;
  isLoading: boolean;
  error: string | null;
}

export function useDiversification(accountNumber: string | null): UseDiversificationResult {
  const [data, setData] = useState<DiversificationSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accountNumber) {
      setData(null);
      setError(null);
      return;
    }

    let isActive = true;
    setIsLoading(true);
    setError(null);

    fetchPortfolioDiversification(accountNumber)
      .then((result) => {
        if (isActive) {
          setData(result);
        }
      })
      .catch((err) => {
        if (!isActive) {
          return;
        }
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError('An unexpected error occurred. Please try again.');
        }
      })
      .finally(() => {
        if (isActive) {
          setIsLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [accountNumber]);

  return { data, isLoading, error };
}
