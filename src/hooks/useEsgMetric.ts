import { useCallback, useEffect, useState } from 'react';
import { ApiError, fetchEsgMetric } from '../services/api';
import type { EsgMetric } from '../types/esg';

export interface EsgMetricState {
  metric: EsgMetric | null;
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
  setMetric: (metric: EsgMetric | null) => void;
}

export function useEsgMetric(accountNumber: string | null): EsgMetricState {
  const [metric, setMetric] = useState<EsgMetric | null>(null);
  const [loading, setLoading] = useState<boolean>(Boolean(accountNumber));
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!accountNumber) {
      setMetric(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setMetric(await fetchEsgMetric(accountNumber));
    } catch (err) {
      setMetric(null);
      setError(err instanceof ApiError ? err.message : 'Unable to load carbon intensity.');
    } finally {
      setLoading(false);
    }
  }, [accountNumber]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { metric, loading, error, reload, setMetric };
}
