import type { PortfolioSummary } from '../types/account';
import type { EsgMetric, EsgAuditResponse } from '../types/esg';

const API_BASE_URL = 'http://localhost:8000/api';

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public statusText?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function fetchPortfolio(accountNumber: string): Promise<PortfolioSummary> {
  try {
    const response = await fetch(`${API_BASE_URL}/portfolio/${accountNumber}`);
    
    if (!response.ok) {
      if (response.status === 400) {
        const errorData = await response.json();
        throw new ApiError(errorData.detail || 'Invalid account number', response.status, response.statusText);
      }
      throw new ApiError(`HTTP ${response.status}: ${response.statusText}`, response.status, response.statusText);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ApiError('Unable to connect to the server. Please ensure the backend is running.');
    }
    throw new ApiError('An unexpected error occurred while fetching portfolio data.');
  }
}

export async function fetchTransactions(accountNumber: string): Promise<{
  accountNumber: string;
  transactions: any[];
  message: string;
}> {
  try {
    const response = await fetch(`${API_BASE_URL}/transactions/${accountNumber}`);
    
    if (!response.ok) {
      if (response.status === 400) {
        const errorData = await response.json();
        throw new ApiError(errorData.detail || 'Invalid account number', response.status, response.statusText);
      }
      throw new ApiError(`HTTP ${response.status}: ${response.statusText}`, response.status, response.statusText);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ApiError('Unable to connect to the server. Please ensure the backend is running.');
    }
    throw new ApiError('An unexpected error occurred while fetching transaction data.');
  }
}

// ---- ESG carbon intensity (RP-48, RP-50, RP-51) ----

function extractDetail(errorData: any, fallback: string): string {
  const detail = errorData?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((d: any) => d?.msg ?? JSON.stringify(d)).join('; ');
  }
  return fallback;
}

async function esgRequest<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch (error) {
    throw new ApiError('Unable to connect to the server. Please ensure the backend is running.');
  }
  if (!response.ok) {
    let errorData: any = null;
    try {
      errorData = await response.json();
    } catch {
      errorData = null;
    }
    throw new ApiError(extractDetail(errorData, `HTTP ${response.status}: ${response.statusText}`), response.status, response.statusText);
  }
  return (await response.json()) as T;
}

/** Returns null when the account has no carbon intensity metric yet (404). */
export async function fetchEsgMetric(accountNumber: string): Promise<EsgMetric | null> {
  try {
    return await esgRequest<EsgMetric>(`/portfolio/${accountNumber}/esg`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function putEsgOverride(accountNumber: string, value: number, reason: string): Promise<EsgMetric> {
  return esgRequest<EsgMetric>(`/portfolio/${accountNumber}/esg/override`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ value, reason }),
  });
}

export async function deleteEsgOverride(accountNumber: string, reason: string): Promise<EsgMetric> {
  return esgRequest<EsgMetric>(`/portfolio/${accountNumber}/esg/override`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  });
}

export async function fetchEsgAudit(accountNumber: string): Promise<EsgAuditResponse> {
  return esgRequest<EsgAuditResponse>(`/portfolio/${accountNumber}/esg/audit`);
}
