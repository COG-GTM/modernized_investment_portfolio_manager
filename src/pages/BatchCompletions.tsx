import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button } from '../components';
import { ApiError } from '../services/api';
import {
  BatchJobRecord,
  BatchStatus,
  ReplayTrace,
  fetchBatchJobs,
  fetchBatchStatus,
  runReplay,
  runRetrySafetyCheck,
} from '../services/batchApi';

const shortSha = (sha: string | null | undefined) => (sha ? sha.slice(0, 12) : '-');
const shortId = (id: string | null | undefined) => (id ? id.slice(0, 8) : '-');

function Badge({ tone, children }: { tone: 'ok' | 'bad' | 'warn' | 'muted'; children: React.ReactNode }) {
  const tones = {
    ok: 'bg-green-100 text-green-800 border-green-300',
    bad: 'bg-red-100 text-red-800 border-red-300',
    warn: 'bg-amber-100 text-amber-800 border-amber-300',
    muted: 'bg-muted text-muted-foreground border-border',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded border text-xs font-semibold ${tones[tone]}`}>
      {children}
    </span>
  );
}

export default function BatchCompletions() {
  const [status, setStatus] = useState<BatchStatus | null>(null);
  const [jobs, setJobs] = useState<BatchJobRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [liveReplay, setLiveReplay] = useState<ReplayTrace | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [s, j] = await Promise.all([fetchBatchStatus(), fetchBatchJobs()]);
      setStatus(s);
      setJobs(j.jobs);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unexpected error loading batch data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleReplay = async (jobId: string) => {
    setBusy(`replay:${jobId}`);
    setError(null);
    try {
      const trace = await runReplay(jobId);
      setLiveReplay(trace);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Replay failed.');
    } finally {
      setBusy(null);
    }
  };

  const handleCheck = async () => {
    setBusy('check');
    setError(null);
    try {
      await runRetrySafetyCheck();
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Check failed.');
    } finally {
      setBusy(null);
    }
  };

  const lastCheck = status?.last_check ?? null;
  const duplicateJobs = jobs.filter((j) => j.completion_count > 1).length;

  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="lg">
        <div className="space-y-8">
          <div className="flex items-center justify-between">
            <Link to={ROUTES.MAIN_MENU}>
              <Button variant="secondary" size="sm">← Back to Main Menu</Button>
            </Link>
            <Badge tone="warn">Synthetic demonstration</Badge>
          </div>
          <PageHeader
            title="Batch Completions"
            subtitle="End-of-day posting jobs, attempts and completion records per logical job"
          />

          {error && (
            <div role="alert" className="rounded-lg border border-red-300 bg-red-50 text-red-800 px-4 py-3 text-sm">
              {error}
            </div>
          )}

          <main className="space-y-6 animate-slide-up">
            <div className="grid gap-4 md:grid-cols-3">
              <Card padding="sm">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Code revision</p>
                <p className="font-mono text-sm mt-1" data-testid="code-revision">{shortSha(status?.code_revision)}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  scenario: <span className="font-mono">{status?.scenario ?? '-'}</span>
                  {status?.fault_injection_enabled ? ' · fault injector armed' : ' · fault injector off'}
                </p>
              </Card>
              <Card padding="sm">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Retry-safety check</p>
                <div className="mt-1 flex items-center gap-2" data-testid="check-result">
                  {lastCheck ? (
                    <Badge tone={lastCheck.result === 'PASS' ? 'ok' : 'bad'}>{lastCheck.result}</Badge>
                  ) : (
                    <Badge tone="muted">not run</Badge>
                  )}
                  <span className="text-xs text-muted-foreground">
                    {lastCheck ? `${lastCheck.finished_at} @ ${shortSha(lastCheck.code_revision)}` : 'no saved result'}
                  </span>
                </div>
                <Button size="sm" className="mt-3" onClick={handleCheck} disabled={busy !== null}>
                  {busy === 'check' ? 'Running check…' : 'Run check-retry-safety'}
                </Button>
              </Card>
              <Card padding="sm">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Invariant</p>
                <p className="text-sm mt-1">Exactly one completion per logical job</p>
                <div className="mt-2" data-testid="duplicate-summary">
                  {duplicateJobs > 0 ? (
                    <Badge tone="bad">{duplicateJobs} job(s) with duplicate completions</Badge>
                  ) : (
                    <Badge tone="ok">no duplicates</Badge>
                  )}
                </div>
              </Card>
            </div>

            {lastCheck && (
              <Card padding="sm">
                <h3 className="text-sm font-semibold mb-2">Saved check probes (from last run)</h3>
                <ul className="space-y-1">
                  {lastCheck.probes.map((p) => (
                    <li key={p.name} className="flex items-start gap-2 text-sm min-w-0">
                      <Badge tone={p.passed ? 'ok' : 'bad'}>{p.passed ? 'PASS' : 'FAIL'}</Badge>
                      <span className="font-mono text-xs break-all min-w-0">{p.name}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            )}

            <section className="space-y-4">
              <h2 className="text-xl font-semibold">Jobs and completion records</h2>
              {loading && <p className="text-sm text-muted-foreground">Loading…</p>}
              {!loading && jobs.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  No jobs seeded. Run <code className="font-mono">python -m techfest_batch seed</code> in backend/.
                </p>
              )}
              {jobs.map((job) => {
                const duplicate = job.completion_count > 1;
                return (
                  <Card key={job.job_id} padding="sm" className={duplicate ? 'border-red-400 ring-1 ring-red-300' : ''}>
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <p className="font-mono text-sm font-semibold">{job.job_id}</p>
                        <p className="text-xs text-muted-foreground">
                          {job.portfolio_id} · run {job.run_date} · {job.transaction_count} txns · total {job.total_amount}
                          {job.fault_injection ? ` · fault: ${job.fault_injection}` : ''}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge tone={job.status === 'COMPLETED' ? 'ok' : 'muted'}>{job.status}</Badge>
                        <Badge tone={duplicate ? 'bad' : job.completion_count === 1 ? 'ok' : 'muted'}>
                          {job.completion_count} completion{job.completion_count === 1 ? '' : 's'}
                          {duplicate ? ' — DUPLICATE' : ''}
                        </Badge>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleReplay(job.job_id)}
                          disabled={busy !== null}
                        >
                          {busy === `replay:${job.job_id}` ? 'Replaying…' : 'Replay retries'}
                        </Button>
                      </div>
                    </div>
                    {job.completions.length > 0 && (
                      <div className="mt-3 overflow-x-auto">
                        <table className="w-full text-xs">
                          <thead className="text-muted-foreground text-left">
                            <tr>
                              <th className="py-1 pr-3">completion</th>
                              <th className="py-1 pr-3">attempt</th>
                              <th className="py-1 pr-3">request id</th>
                              <th className="py-1 pr-3">completed at</th>
                              <th className="py-1 pr-3">revision</th>
                            </tr>
                          </thead>
                          <tbody className="font-mono">
                            {job.completions.map((c) => (
                              <tr key={c.completion_id} className={duplicate ? 'text-red-800' : ''}>
                                <td className="py-1 pr-3">{shortId(c.completion_id)}</td>
                                <td className="py-1 pr-3">{c.attempt}</td>
                                <td className="py-1 pr-3">{shortId(c.request_id)}</td>
                                <td className="py-1 pr-3">{c.completed_at}</td>
                                <td className="py-1 pr-3">{shortSha(c.code_revision)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </Card>
                );
              })}
            </section>

            <ReplaySection title="Live replay (this browser session)" trace={liveReplay} />
            <ReplaySection title="Saved replay trace (last run on this service)" trace={status?.last_replay ?? null} />
          </main>
        </div>
      </Container>
    </div>
  );
}

function ReplaySection({ title, trace }: { title: string; trace: ReplayTrace | null }) {
  return (
    <Card padding="sm">
      <h3 className="text-sm font-semibold mb-2">{title}</h3>
      {!trace ? (
        <p className="text-xs text-muted-foreground">No trace yet.</p>
      ) : (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground">
            job <span className="font-mono">{trace.job_id}</span> · scenario {trace.scenario} · revision{' '}
            <span className="font-mono">{shortSha(trace.code_revision)}</span> · timeout {trace.client_timeout_s}s ·
            stall {trace.stall_ms}ms · completions {trace.completions_before} → {trace.completions_after}
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="text-muted-foreground text-left">
                <tr>
                  <th className="py-1 pr-3">attempt</th>
                  <th className="py-1 pr-3">request id</th>
                  <th className="py-1 pr-3">started</th>
                  <th className="py-1 pr-3">code</th>
                  <th className="py-1 pr-3">outcome</th>
                  <th className="py-1 pr-3">completion</th>
                  <th className="py-1 pr-3">revision</th>
                </tr>
              </thead>
              <tbody className="font-mono">
                {trace.attempts.map((a) => (
                  <tr key={a.request_id}>
                    <td className="py-1 pr-3">{a.attempt}</td>
                    <td className="py-1 pr-3">{shortId(a.request_id)}</td>
                    <td className="py-1 pr-3">{a.started_at}</td>
                    <td className="py-1 pr-3">{a.status_code ?? '-'}</td>
                    <td className="py-1 pr-3">{a.outcome}</td>
                    <td className="py-1 pr-3">{shortId(a.completion_id)}</td>
                    <td className="py-1 pr-3">{shortSha(a.code_revision)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Badge tone={trace.duplicate_detected ? 'bad' : 'ok'}>
            {trace.duplicate_detected ? 'DUPLICATE COMPLETION DETECTED' : 'single completion — invariant holds'}
          </Badge>
        </div>
      )}
    </Card>
  );
}
