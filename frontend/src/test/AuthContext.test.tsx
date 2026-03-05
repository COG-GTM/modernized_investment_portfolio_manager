import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from '../contexts/AuthContext';

// Mock the api module
vi.mock('../services/api', () => ({
  authApi: {
    login: vi.fn(),
  },
}));

function TestConsumer() {
  const { isAuthenticated, user, login, logout } = useAuth();
  return (
    <div>
      <div data-testid="auth-status">{isAuthenticated ? 'authenticated' : 'not-authenticated'}</div>
      <div data-testid="username">{user?.username ?? 'none'}</div>
      <button onClick={() => login({ username: 'testuser', password: 'pass' })}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

function renderWithProviders() {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    </BrowserRouter>
  );
}

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('starts unauthenticated', () => {
    renderWithProviders();
    expect(screen.getByTestId('auth-status').textContent).toBe('not-authenticated');
    expect(screen.getByTestId('username').textContent).toBe('none');
  });

  it('authenticates on successful login', async () => {
    const { authApi } = await import('../services/api');
    vi.mocked(authApi.login).mockResolvedValue({
      token: 'test-token-123',
      username: 'testuser',
    });

    renderWithProviders();
    fireEvent.click(screen.getByText('Login'));

    await waitFor(() => {
      expect(screen.getByTestId('auth-status').textContent).toBe('authenticated');
      expect(screen.getByTestId('username').textContent).toBe('testuser');
    });
  });

  it('clears auth state on logout', async () => {
    const { authApi } = await import('../services/api');
    vi.mocked(authApi.login).mockResolvedValue({
      token: 'test-token-123',
      username: 'testuser',
    });

    renderWithProviders();
    fireEvent.click(screen.getByText('Login'));

    await waitFor(() => {
      expect(screen.getByTestId('auth-status').textContent).toBe('authenticated');
    });

    fireEvent.click(screen.getByText('Logout'));

    expect(screen.getByTestId('auth-status').textContent).toBe('not-authenticated');
    expect(screen.getByTestId('username').textContent).toBe('none');
  });

  it('restores auth from localStorage', () => {
    localStorage.setItem('jwt_token', 'stored-token');
    localStorage.setItem('auth_user', 'storeduser');

    renderWithProviders();
    expect(screen.getByTestId('auth-status').textContent).toBe('authenticated');
    expect(screen.getByTestId('username').textContent).toBe('storeduser');
  });
});
