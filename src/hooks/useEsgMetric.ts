import { useCallback, useEffect, useRef, useState } from 'react';
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
  const [error, setError] = useState<string | null>(null);
  const [settledFor, setSettledFor] = useState<string | null>(null);
  const [reloading, setReloading] = useState(false);
  const requestId = useRef(0);

  const reload = useCallback(async () => {
    const id = ++requestId.current;
    if (!accountNumber) {
      setMetric(null);
      setError(null);
      setSettledFor(null);
      setReloading(false);
      return;
    }
    setReloading(true);
    setError(null);
    try {
      const result = await fetchEsgMetric(accountNumber);
      if (id !== requestId.current) return;
      setMetric(result);
    } catch (err) {
      if (id !== requestId.current) return;
      setMetric(null);
      setError(err instanceof ApiError ? err.message : 'Unable to load carbon intensity.');
    } finally {
      if (id === requestId.current) {
        setSettledFor(accountNumber);
        setReloading(false);
      }
    }
  }, [accountNumber]);

  useEffect(() => {
    reload();
  }, [reload]);

  // Loading is derived, so the first render after the account changes never shows the empty state.
  const loading = Boolean(accountNumber) && (reloading || settledFor !== accountNumber);
  const current = accountNumber && settledFor === accountNumber ? metric : null;

  return { metric: loading ? null : current, loading, error: loading ? null : error, reload, setMetric };
}
