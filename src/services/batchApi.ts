import { ApiError } from './api';

const BATCH_BASE_URL = 'http://localhost:8000/batch';

export interface BatchCompletionRecord {
  completion_id: string;
  job_id: string;
  attempt: number;
  request_id: string;
  completed_at: string | null;
  code_revision: string;
}

export interface BatchJobRecord {
  job_id: string;
  run_date: string;
  portfolio_id: string;
  job_type: string;
  status: string;
  transaction_count: number;
  total_amount: string;
  fault_injection: string | null;
  created_at: string | null;
  completions: BatchCompletionRecord[];
  completion_count: number;
}

export interface AttemptTrace {
  attempt: number;
  request_id: string;
  started_at: string;
  finished_at: string | null;
  status_code: number | null;
  outcome: string;
  completion_id: string | null;
  deduplicated: boolean | null;
  code_revision: string | null;
  error: string | null;
}

export interface ReplayTrace {
  job_id: string;
  scenario: string;
  code_revision: string;
  client_timeout_s: number;
  client_max_attempts: number;
  stall_ms: number;
  started_at: string;
  finished_at: string;
  attempts: AttemptTrace[];
  final_completion_id: string | null;
  completions_before: number;
  completions_after: number;
  duplicate_detected: boolean;
}

export interface CheckProbe {
  name: string;
  passed: boolean;
  details: Record<string, unknown>;
}

export interface CheckResult {
  check: string;
  result: 'PASS' | 'FAIL';
  scenario: string;
  code_revision: string;
  started_at: string;
  finished_at: string;
  probes: CheckProbe[];
}

export interface BatchStatus {
  label: string;
  scenario: string;
  fault_injection_enabled: boolean;
  code_revision: string;
  stall_ms: number;
  client_timeout_s: number;
  client_max_attempts: number;
  last_check: CheckResult | null;
  last_replay: ReplayTrace | null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BATCH_BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    });
  } catch {
    throw new ApiError('Unable to connect to the batch service. Please ensure the backend is running.');
  }
  if (!response.ok) {
    let detail = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const body = await response.json();
      if (body.detail) detail = body.detail;
    } catch {
      // keep default detail
    }
    throw new ApiError(detail, response.status, response.statusText);
  }
  return response.json() as Promise<T>;
}

export function fetchBatchStatus(): Promise<BatchStatus> {
  return request<BatchStatus>('/status');
}

export function fetchBatchJobs(): Promise<{ jobs: BatchJobRecord[] }> {
  return request<{ jobs: BatchJobRecord[] }>('/jobs');
}

export function runReplay(jobId: string): Promise<ReplayTrace> {
  return request<ReplayTrace>('/replay', { method: 'POST', body: JSON.stringify({ job_id: jobId }) });
}

export function runRetrySafetyCheck(): Promise<CheckResult> {
  return request<CheckResult>('/check-retry-safety', { method: 'POST' });
}
