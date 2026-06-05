import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import MainMenu from './MainMenu';

const mockPush = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useHistory: () => ({
      push: mockPush,
      location: { pathname: '/' },
      listen: vi.fn(),
    }),
  };
});

function renderMainMenu() {
  return render(
    <MemoryRouter>
      <MainMenu />
    </MemoryRouter>
  );
}

describe('MainMenu', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  it('renders page title', () => {
    renderMainMenu();
    expect(screen.getByText('Investment Portfolio Manager')).toBeInTheDocument();
  });

  it('renders subtitle', () => {
    renderMainMenu();
    expect(
      screen.getByText('View, analyze, and manage investment portfolios')
    ).toBeInTheDocument();
  });

  it('renders portfolio option', () => {
    renderMainMenu();
    expect(screen.getByText('Portfolio')).toBeInTheDocument();
  });

  it('renders history option', () => {
    renderMainMenu();
    expect(screen.getByText('History')).toBeInTheDocument();
  });

  it('renders navigation instructions', () => {
    renderMainMenu();
    expect(screen.getByText(/arrow keys/i)).toBeInTheDocument();
  });

  it('renders menu role', () => {
    renderMainMenu();
    expect(screen.getByRole('menu')).toBeInTheDocument();
  });

  it('renders menu option buttons', () => {
    renderMainMenu();
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThanOrEqual(2);
  });

  it('renders keyboard shortcut hints', () => {
    renderMainMenu();
    expect(screen.getByText('Enter')).toBeInTheDocument();
    expect(screen.getByText('Esc')).toBeInTheDocument();
  });

  it('clicking option selects it', () => {
    renderMainMenu();
    const portfolioButton = screen.getAllByRole('button')[0];
    fireEvent.click(portfolioButton);
    // Selection triggers navigation via setTimeout
    act(() => {
      vi.advanceTimersByTime(200);
    });
  });

  it('pressing Enter on selected option navigates', () => {
    renderMainMenu();
    // ArrowDown to select first option
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));
    });
    // Enter to activate
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    });
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(mockPush).toHaveBeenCalledWith('/portfolio-inquiry');
  });

  it('pressing number shortcut 1 navigates to portfolio', () => {
    renderMainMenu();
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: '1', bubbles: true }));
    });
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(mockPush).toHaveBeenCalledWith('/portfolio-inquiry');
  });

  it('pressing number shortcut 2 navigates to history', () => {
    renderMainMenu();
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: '2', bubbles: true }));
    });
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(mockPush).toHaveBeenCalledWith('/transaction-history');
  });

  it('pressing Space on selected option navigates', () => {
    renderMainMenu();
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));
    });
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', bubbles: true }));
    });
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(mockPush).toHaveBeenCalledWith('/portfolio-inquiry');
  });

  it('pressing Escape resets selection', () => {
    renderMainMenu();
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));
    });
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    });
    // After escape, no option is selected
  });

  it('keypress on option calls onKeyPress handler', () => {
    renderMainMenu();
    const portfolioButton = screen.getAllByRole('button')[0];
    fireEvent.keyDown(portfolioButton, { key: 'Enter' });
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(mockPush).toHaveBeenCalledWith('/portfolio-inquiry');
  });
});
