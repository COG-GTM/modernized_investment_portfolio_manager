import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import MainMenu from '../pages/MainMenu';

// Mock AuthContext
vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { username: 'testuser', token: 'token' },
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

describe('MainMenu', () => {
  it('renders the main menu title', () => {
    render(
      <MemoryRouter>
        <MainMenu />
      </MemoryRouter>
    );
    expect(screen.getByText('Portfolio Management System')).toBeInTheDocument();
  });

  it('renders all menu options', () => {
    render(
      <MemoryRouter>
        <MainMenu />
      </MemoryRouter>
    );
    expect(screen.getByText('Portfolio Position Inquiry')).toBeInTheDocument();
    expect(screen.getByText('Transaction History')).toBeInTheDocument();
    expect(screen.getByText('Exit')).toBeInTheDocument();
  });

  it('renders shortcut keys', () => {
    render(
      <MemoryRouter>
        <MainMenu />
      </MemoryRouter>
    );
    // Shortcut keys appear in both the menu option badge and the keyboard hint area
    expect(screen.getAllByText('1').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('2').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('3').length).toBeGreaterThanOrEqual(1);
  });

  it('shows logged in user', () => {
    render(
      <MemoryRouter>
        <MainMenu />
      </MemoryRouter>
    );
    expect(screen.getByText('testuser')).toBeInTheDocument();
  });

  it('renders with correct accessibility roles', () => {
    render(
      <MemoryRouter>
        <MainMenu />
      </MemoryRouter>
    );
    expect(screen.getByRole('menu')).toBeInTheDocument();
    expect(screen.getAllByRole('menuitem')).toHaveLength(3);
  });
});
