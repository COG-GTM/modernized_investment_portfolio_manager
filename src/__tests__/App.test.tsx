import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';

describe('App', () => {
  it('renders main menu on default route', () => {
    render(<App />);
    expect(screen.getByText('Investment Portfolio Manager')).toBeInTheDocument();
  });

  it('renders portfolio inquiry page', () => {
    window.history.pushState({}, '', '/portfolio-inquiry');
    render(<App />);
    expect(screen.getByText('Portfolio Inquiry')).toBeInTheDocument();
  });

  it('renders transaction history page', () => {
    window.history.pushState({}, '', '/transaction-history');
    render(<App />);
    expect(screen.getByText('Transaction History')).toBeInTheDocument();
  });
});
