/**
 * Gap hunt (RP-49): dashboard loading / empty / error states driven by useEsgMetric and fetchEsgMetric.
 */
import { render, screen, waitFor, act } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import CarbonIntensityCard from '../../CarbonIntensityCard';
import { useEsgMetric } from '../../../hooks/useEsgMetric';
import { computedMetric, overriddenMetric } from '../../../test/esgFixtures';

type RenderLog = Array<{ loading: boolean; metric: boolean; error: string | null }>;

function Harness({ account, log }: { account: string | null; log: RenderLog }) {
  const esg = useEsgMetric(account);
  log.push({ loading: esg.loading, metric: esg.metric !== null, error: esg.error });
  return <CarbonIntensityCard metric={esg.metric} loading={esg.loading} error={esg.error} />;
}

function jsonResponse(body: unknown, status = 200) {
  return { ok: status < 400, status, statusText: 'x', json: async () => body } as unknown as Response;
}

function deferred<T>() {
  let resolve!: (v: T) => void;
  const promise = new Promise<T>((r) => (resolve = r));
  return { promise, resolve };
}

describe('useEsgMetric gaps (RP-49)', () => {
  const fetchMock = vi.fn();
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal('fetch', fetchMock);
  });
  afterEach(() => vi.unstubAllGlobals());

  it('never flashes the empty state between selecting an account and the first response', async () => {
    /** RP-49: before the fix the first render after the account changed had loading=false and metric=null,
     * so "Not available" was painted for one frame before "Loading carbon intensity..." appeared. */
    const pending = deferred<Response>();
    fetchMock.mockReturnValue(pending.promise);
    const log: RenderLog = [];
    const { rerender } = render(<Harness account={null} log={log} />);
    log.length = 0;
    rerender(<Harness account="1234567890" log={log} />);

    expect(screen.getByRole('status')).toHaveTextContent(/Loading/);
    expect(log.some((entry) => !entry.loading && !entry.metric && entry.error === null)).toBe(false);

    await act(async () => {
      pending.resolve(jsonResponse(computedMetric));
      await pending.promise;
    });
    await waitFor(() => expect(screen.getByTestId('carbon-intensity-value')).toBeInTheDocument());
  });

  it('ignores a stale response when the account changes before it resolves', async () => {
    /** RP-49: switching accounts quickly could let the slower first request overwrite the second
     * account's metric (and its override indicator) with the wrong portfolio's data. */
    const first = deferred<Response>();
    const second = deferred<Response>();
    fetchMock.mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
    const log: RenderLog = [];
    const { rerender } = render(<Harness account="1111111111" log={log} />);
    rerender(<Harness account="2222222222" log={log} />);

    await act(async () => {
      second.resolve(jsonResponse(computedMetric));
      await second.promise;
    });
    await waitFor(() => expect(screen.queryByTestId('override-indicator')).not.toBeInTheDocument());
    await act(async () => {
      first.resolve(jsonResponse({ ...overriddenMetric, account_number: '1111111111' }));
      await first.promise;
    });

    expect(screen.queryByTestId('override-indicator')).not.toBeInTheDocument();
    expect(screen.getByTestId('carbon-intensity-value')).toHaveTextContent('1.31');
  });

  it('renders the empty state for a 200 payload with has_metric=false', async () => {
    /** RP-48/RP-49: a known account with no computed month is the empty state. */
    fetchMock.mockResolvedValue(jsonResponse({ ...computedMetric, has_metric: false, source: 'none', as_of_month: null, effective_value: null, computed_value: null, coverage_pct: null, computed_at: null }));
    render(<Harness account="1234567890" log={[]} />);
    await waitFor(() => expect(screen.getByTestId('carbon-intensity-empty')).toBeInTheDocument());
  });

  it('shows an error, not the empty state, when the account is unknown (404)', async () => {
    /** RP-49: before the fix every 404 was mapped to "Not available", hiding a misrouted or unknown account. */
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'Account 1234567890 not found' }, 404));
    render(<Harness account="1234567890" log={[]} />);
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(/not found/));
    expect(screen.queryByTestId('carbon-intensity-empty')).not.toBeInTheDocument();
  });

  it('shows a connection error when the backend is unreachable', async () => {
    /** RP-49: network failure must not look like "no emissions data". */
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'));
    render(<Harness account="1234567890" log={[]} />);
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(/Unable to connect/));
    expect(screen.queryByTestId('carbon-intensity-empty')).not.toBeInTheDocument();
  });
});
