import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import LoadingSpinner from '../../components/LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders with role status', () => {
    render(<LoadingSpinner />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('has sr-only loading text', () => {
    render(<LoadingSpinner />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('applies sm size', () => {
    const { container } = render(<LoadingSpinner size="sm" />);
    expect(container.firstChild).toHaveClass('w-4');
  });

  it('applies md size by default', () => {
    const { container } = render(<LoadingSpinner />);
    expect(container.firstChild).toHaveClass('w-6');
  });

  it('applies lg size', () => {
    const { container } = render(<LoadingSpinner size="lg" />);
    expect(container.firstChild).toHaveClass('w-8');
  });

  it('applies custom className', () => {
    const { container } = render(<LoadingSpinner className="ml-2" />);
    expect(container.firstChild).toHaveClass('ml-2');
  });
});
