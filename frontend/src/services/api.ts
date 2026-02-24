import axios from 'axios';
import type {
  PortfolioSummary,
  TransactionHistoryResponse,
  LoginCredentials,
  LoginResponse,
} from '../types';

const TOKEN_KEY = 'jwt_token';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 and token expiry
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      const isLoginRequest = error.config?.url?.includes('/auth/login');
      if (!isLoginRequest) {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem('auth_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

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

function handleApiError(error: unknown): never {
  if (error instanceof ApiError) {
    throw error;
  }
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    const detail = error.response?.data?.detail;
    const statusText = error.response?.statusText ?? 'Unknown Error';
    throw new ApiError(
      detail || `HTTP ${status}: ${statusText}`,
      status,
      statusText
    );
  }
  if (error instanceof Error && error.message.includes('Network Error')) {
    throw new ApiError(
      'Unable to connect to the server. Please ensure the backend is running.'
    );
  }
  throw new ApiError('An unexpected error occurred.');
}

export const authApi = {
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      const response = await api.post<LoginResponse>(
        '/auth/login',
        credentials
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },
};

export const portfolioApi = {
  async getPortfolio(id: string): Promise<PortfolioSummary> {
    try {
      const response = await api.get<PortfolioSummary>(`/portfolios/${id}`);
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },

  async getHistory(
    id: string,
    page: number = 1,
    pageSize: number = 10
  ): Promise<TransactionHistoryResponse> {
    try {
      const response = await api.get<TransactionHistoryResponse>(
        `/portfolios/${id}/history`,
        {
          params: { page, pageSize },
        }
      );
      return response.data;
    } catch (error) {
      handleApiError(error);
    }
  },
};

export default api;
