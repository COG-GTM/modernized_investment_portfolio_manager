import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import LoadingButton from './LoadingButton';

describe('LoadingButton', () => {
  it('renders children', () => {
    render(<LoadingButton>Submit</LoadingButton>);
    expect(screen.getByText('Submit')).toBeInTheDocument();
  });

  it('shows spinner when loading', () => {
    render(<LoadingButton loading>Submit</LoadingButton>);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('is disabled when loading', () => {
    render(<LoadingButton loading>Submit</LoadingButton>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('is disabled when disabled prop is set', () => {
    render(<LoadingButton disabled>Submit</LoadingButton>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('is not disabled by default', () => {
    render(<LoadingButton>Submit</LoadingButton>);
    expect(screen.getByRole('button')).not.toBeDisabled();
  });

  it('renders primary variant by default', () => {
    render(<LoadingButton>Submit</LoadingButton>);
    const btn = screen.getByRole('button');
    expect(btn.className).toContain('bg-primary');
  });

  it('renders secondary variant', () => {
    render(<LoadingButton variant="secondary">Submit</LoadingButton>);
    const btn = screen.getByRole('button');
    expect(btn.className).toContain('bg-secondary');
  });

  it('renders outline variant', () => {
    render(<LoadingButton variant="outline">Submit</LoadingButton>);
    const btn = screen.getByRole('button');
    expect(btn.className).toContain('border');
  });

  it('renders sm size', () => {
    render(<LoadingButton size="sm">Submit</LoadingButton>);
    const btn = screen.getByRole('button');
    expect(btn.className).toContain('px-3');
  });

  it('renders lg size', () => {
    render(<LoadingButton size="lg">Submit</LoadingButton>);
    const btn = screen.getByRole('button');
    expect(btn.className).toContain('px-6');
  });

  it('passes onClick handler', () => {
    const onClick = vi.fn();
    render(<LoadingButton onClick={onClick}>Click</LoadingButton>);
    screen.getByRole('button').click();
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('applies custom className', () => {
    render(<LoadingButton className="extra">Submit</LoadingButton>);
    const btn = screen.getByRole('button');
    expect(btn.className).toContain('extra');
  });
});
