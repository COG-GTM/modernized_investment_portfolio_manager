import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import LoadingSpinner from './LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders with role status', () => {
    render(<LoadingSpinner />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('has sr-only loading text', () => {
    render(<LoadingSpinner />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders sm size', () => {
    render(<LoadingSpinner size="sm" />);
    const spinner = screen.getByRole('status');
    expect(spinner.className).toContain('w-4');
  });

  it('renders md size by default', () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByRole('status');
    expect(spinner.className).toContain('w-6');
  });

  it('renders lg size', () => {
    render(<LoadingSpinner size="lg" />);
    const spinner = screen.getByRole('status');
    expect(spinner.className).toContain('w-8');
  });

  it('applies custom className', () => {
    render(<LoadingSpinner className="my-class" />);
    const spinner = screen.getByRole('status');
    expect(spinner.className).toContain('my-class');
  });

  it('has animate-spin class', () => {
    render(<LoadingSpinner />);
    const spinner = screen.getByRole('status');
    expect(spinner.className).toContain('animate-spin');
  });

  it('has aria-label', () => {
    render(<LoadingSpinner />);
    expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Loading');
  });
});
