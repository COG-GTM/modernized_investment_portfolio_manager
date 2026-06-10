import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import MainMenu from '../../pages/MainMenu';

function renderMainMenu() {
  return render(
    <MemoryRouter>
      <MainMenu />
    </MemoryRouter>
  );
}

describe('MainMenu', () => {
  it('renders title', () => {
    renderMainMenu();
    expect(screen.getByText('Investment Portfolio Manager')).toBeInTheDocument();
  });

  it('renders subtitle', () => {
    renderMainMenu();
    expect(screen.getByText('View, analyze, and manage investment portfolios')).toBeInTheDocument();
  });

  it('renders menu options', () => {
    renderMainMenu();
    expect(screen.getByText('Portfolio')).toBeInTheDocument();
    expect(screen.getByText('History')).toBeInTheDocument();
  });

  it('renders keyboard navigation instructions', () => {
    renderMainMenu();
    expect(screen.getByText(/arrow keys/i)).toBeInTheDocument();
  });

  it('has navigation menu role', () => {
    renderMainMenu();
    expect(screen.getByRole('menu')).toBeInTheDocument();
  });

  it('renders shortcut badges', () => {
    renderMainMenu();
    expect(screen.getAllByText('1').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('2').length).toBeGreaterThanOrEqual(1);
  });
});
