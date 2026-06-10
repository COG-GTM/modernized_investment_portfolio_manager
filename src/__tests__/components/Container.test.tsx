import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Container from '../../components/Container';

describe('Container', () => {
  it('renders children', () => {
    render(<Container>Content</Container>);
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('uses lg size by default', () => {
    const { container } = render(<Container>X</Container>);
    expect(container.firstChild).toHaveClass('max-w-6xl');
  });

  it('applies sm size', () => {
    const { container } = render(<Container size="sm">X</Container>);
    expect(container.firstChild).toHaveClass('max-w-2xl');
  });

  it('applies md size', () => {
    const { container } = render(<Container size="md">X</Container>);
    expect(container.firstChild).toHaveClass('max-w-4xl');
  });

  it('applies xl size', () => {
    const { container } = render(<Container size="xl">X</Container>);
    expect(container.firstChild).toHaveClass('max-w-7xl');
  });

  it('applies full size', () => {
    const { container } = render(<Container size="full">X</Container>);
    expect(container.firstChild).toHaveClass('max-w-full');
  });

  it('applies padding by default', () => {
    const { container } = render(<Container>X</Container>);
    expect(container.firstChild).toHaveClass('px-4');
  });

  it('no padding when padding=false', () => {
    const { container } = render(<Container padding={false}>X</Container>);
    const el = container.firstChild as HTMLElement;
    expect(el.className).not.toContain('px-4');
  });

  it('applies custom className', () => {
    const { container } = render(<Container className="custom">X</Container>);
    expect(container.firstChild).toHaveClass('custom');
  });
});
