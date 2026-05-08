import type { PortfolioInquiryResult, TransactionHistoryResult } from '../types/inquiry';

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

export async function fetchPortfolioInquiry(accountNumber: string): Promise<PortfolioInquiryResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/inquiry/portfolio/${accountNumber}`);

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

export async function fetchTransactionHistoryInquiry(accountNumber: string): Promise<TransactionHistoryResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/inquiry/history/${accountNumber}`);

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
    throw new ApiError('An unexpected error occurred while fetching transaction history.');
  }
}
