import type { PortfolioSummary } from '../types/account';

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

export interface VisitorRecord {
  visitorId: string;
  accountNumber: string;
  visitorName: string;
  action: string;
  ipAddress: string;
  timestamp: string;
  duration: string;
}

export interface VisitorsHistoryResponse {
  totalVisits: number;
  visitors: VisitorRecord[];
  lastUpdated: string;
}

export async function fetchVisitorsHistory(): Promise<VisitorsHistoryResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/visitors/history`);

    if (!response.ok) {
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
    throw new ApiError('An unexpected error occurred while fetching visitors history.');
  }
}
