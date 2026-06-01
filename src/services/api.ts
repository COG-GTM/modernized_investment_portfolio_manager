import type { PortfolioSummary, PortfolioInquiryResponse, HistoryInquiryResponse, MenuResponse } from '../types/account';

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

export async function fetchInquiryMenu(): Promise<MenuResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/inquiry/menu`);

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
    throw new ApiError('An unexpected error occurred while fetching menu data.');
  }
}

export async function fetchInquiryPortfolio(accountNumber: string): Promise<PortfolioInquiryResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/inquiry/portfolio/${accountNumber}`);

    if (!response.ok) {
      if (response.status === 400) {
        const errorData = await response.json();
        throw new ApiError(errorData.detail || 'Invalid account number', response.status, response.statusText);
      }
      if (response.status === 404) {
        throw new ApiError('No portfolio found for this account number.', response.status, response.statusText);
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

export async function fetchInquiryHistory(accountNumber: string): Promise<HistoryInquiryResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/inquiry/history/${accountNumber}`);

    if (!response.ok) {
      if (response.status === 400) {
        const errorData = await response.json();
        throw new ApiError(errorData.detail || 'Invalid account number', response.status, response.statusText);
      }
      if (response.status === 404) {
        throw new ApiError('No transaction history found for this account number.', response.status, response.statusText);
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
    throw new ApiError('An unexpected error occurred while fetching transaction history.');
  }
}
