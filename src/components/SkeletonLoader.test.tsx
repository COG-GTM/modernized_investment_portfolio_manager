import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import SkeletonLoader from './SkeletonLoader';

describe('SkeletonLoader', () => {
  it('renders 1 line by default', () => {
    const { container } = render(<SkeletonLoader />);
    const lines = container.querySelectorAll('.bg-muted');
    expect(lines).toHaveLength(1);
  });

  it('renders multiple lines', () => {
    const { container } = render(<SkeletonLoader lines={3} />);
    const lines = container.querySelectorAll('.bg-muted');
    expect(lines).toHaveLength(3);
  });

  it('applies animate-pulse', () => {
    const { container } = render(<SkeletonLoader />);
    expect(container.firstChild).toHaveClass('animate-pulse');
  });

  it('applies custom className', () => {
    const { container } = render(<SkeletonLoader className="custom" />);
    expect(container.firstChild).toHaveClass('custom');
  });

  it('applies custom height', () => {
    const { container } = render(<SkeletonLoader height="h-8" />);
    const line = container.querySelector('.bg-muted');
    expect(line).toHaveClass('h-8');
  });

  it('adds margin-top to subsequent lines', () => {
    const { container } = render(<SkeletonLoader lines={2} />);
    const lines = container.querySelectorAll('.bg-muted');
    expect(lines[0]).not.toHaveClass('mt-2');
    expect(lines[1]).toHaveClass('mt-2');
  });
});
