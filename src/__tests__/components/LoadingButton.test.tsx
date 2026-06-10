import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import LoadingButton from '../../components/LoadingButton';

describe('LoadingButton', () => {
  it('renders children', () => {
    render(<LoadingButton>Submit</LoadingButton>);
    expect(screen.getByText('Submit')).toBeInTheDocument();
  });

  it('shows spinner when loading', () => {
    render(<LoadingButton loading>Submit</LoadingButton>);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('does not show spinner when not loading', () => {
    render(<LoadingButton>Submit</LoadingButton>);
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('is disabled when loading', () => {
    render(<LoadingButton loading>Submit</LoadingButton>);
    expect(screen.getByText('Submit').closest('button')).toBeDisabled();
  });

  it('is disabled when disabled prop set', () => {
    render(<LoadingButton disabled>Submit</LoadingButton>);
    expect(screen.getByText('Submit').closest('button')).toBeDisabled();
  });

  it('calls onClick handler', () => {
    const onClick = vi.fn();
    render(<LoadingButton onClick={onClick}>Click</LoadingButton>);
    fireEvent.click(screen.getByText('Click'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('applies primary variant by default', () => {
    render(<LoadingButton>Btn</LoadingButton>);
    const btn = screen.getByText('Btn').closest('button') as HTMLElement;
    expect(btn.className).toContain('bg-primary');
  });

  it('applies secondary variant', () => {
    render(<LoadingButton variant="secondary">Btn</LoadingButton>);
    const btn = screen.getByText('Btn').closest('button') as HTMLElement;
    expect(btn.className).toContain('bg-secondary');
  });

  it('applies outline variant', () => {
    render(<LoadingButton variant="outline">Btn</LoadingButton>);
    const btn = screen.getByText('Btn').closest('button') as HTMLElement;
    expect(btn.className).toContain('border');
  });
});
