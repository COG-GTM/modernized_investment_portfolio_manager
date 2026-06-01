import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../contexts/AuthContext';
import { ToastProvider } from '../contexts/ToastContext';
import Login from '../pages/Login';

// Mock the api module
vi.mock('../services/api', () => ({
  authApi: {
    login: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    status?: number;
    statusText?: string;
    constructor(message: string, status?: number, statusText?: string) {
      super(message);
      this.name = 'ApiError';
      this.status = status;
      this.statusText = statusText;
    }
  },
}));

function renderLogin() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <ToastProvider>
          <Login />
        </ToastProvider>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('Login', () => {
  it('renders the login form', () => {
    renderLogin();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByLabelText('Username')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
  });

  it('shows error when submitting empty form', async () => {
    renderLogin();
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    await waitFor(() => {
      expect(screen.getByText('Please enter both username and password.')).toBeInTheDocument();
    });
  });

  it('calls login on valid submission', async () => {
    const { authApi } = await import('../services/api');
    vi.mocked(authApi.login).mockResolvedValue({
      token: 'test-token',
      username: 'testuser',
    });

    renderLogin();
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledWith({ username: 'testuser', password: 'password123' });
    });
  });

  it('shows error on failed login', async () => {
    const { authApi, ApiError } = await import('../services/api');
    vi.mocked(authApi.login).mockRejectedValue(new ApiError('Invalid credentials', 401));

    renderLogin();
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'bad' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      // Error appears in both the inline error banner and the toast notification
      const errorElements = screen.getAllByText('Invalid credentials');
      expect(errorElements.length).toBeGreaterThanOrEqual(1);
    });
  });
});
