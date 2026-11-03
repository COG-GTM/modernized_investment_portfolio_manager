import type { PortfolioSummary } from '../types/account';
import type { EsgMetric, EsgOverrideErrors, EsgOverrideRequest } from '../types/esg';

const API_BASE_URL = 'http://localhost:8000/api';

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public statusText?: string,
    public fieldErrors: EsgOverrideErrors = {}
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

interface ValidationErrorItem {
  loc?: (string | number)[];
  msg?: string;
}

function parseFieldErrors(detail: unknown): EsgOverrideErrors {
  const errors: EsgOverrideErrors = {};
  if (!Array.isArray(detail)) return errors;
  for (const item of detail as ValidationErrorItem[]) {
    const field = item.loc?.[item.loc.length - 1];
    if ((field === 'value' || field === 'reason') && item.msg && !errors[field]) {
      errors[field] = item.msg.replace(/^Value error, /, '');
    }
  }
  return errors;
}

async function esgRequest(url: string, init?: RequestInit): Promise<EsgMetric> {
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch {
    throw new ApiError('Unable to connect to the server. Please ensure the backend is running.');
  }

  if (response.ok) {
    return response.json();
  }

  const body = await response.json().catch(() => ({}));
  if (response.status === 422) {
    const fieldErrors = parseFieldErrors(body.detail);
    throw new ApiError('Please correct the highlighted fields.', 422, response.statusText, fieldErrors);
  }
  const message = typeof body.detail === 'string' ? body.detail : `HTTP ${response.status}: ${response.statusText}`;
  throw new ApiError(message, response.status, response.statusText);
}

export function fetchEsgMetric(accountNumber: string): Promise<EsgMetric> {
  return esgRequest(`${API_BASE_URL}/portfolio/${accountNumber}/esg`);
}

export function overrideEsgMetric(accountNumber: string, request: EsgOverrideRequest): Promise<EsgMetric> {
  return esgRequest(`${API_BASE_URL}/portfolio/${accountNumber}/esg/override`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
}
