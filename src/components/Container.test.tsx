import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Container from './Container';

describe('Container', () => {
  it('renders children', () => {
    render(<Container>Content here</Container>);
    expect(screen.getByText('Content here')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<Container className="custom">Text</Container>);
    expect(container.firstChild).toHaveClass('custom');
  });

  it('renders sm size', () => {
    const { container } = render(<Container size="sm">Small</Container>);
    expect(container.firstChild).toHaveClass('max-w-2xl');
  });

  it('renders md size', () => {
    const { container } = render(<Container size="md">Medium</Container>);
    expect(container.firstChild).toHaveClass('max-w-4xl');
  });

  it('renders lg size by default', () => {
    const { container } = render(<Container>Default</Container>);
    expect(container.firstChild).toHaveClass('max-w-6xl');
  });

  it('renders xl size', () => {
    const { container } = render(<Container size="xl">XLarge</Container>);
    expect(container.firstChild).toHaveClass('max-w-7xl');
  });

  it('renders full size', () => {
    const { container } = render(<Container size="full">Full</Container>);
    expect(container.firstChild).toHaveClass('max-w-full');
  });

  it('has padding by default', () => {
    const { container } = render(<Container>Padded</Container>);
    expect(container.firstChild).toHaveClass('px-4');
  });

  it('removes padding when padding=false', () => {
    const { container } = render(<Container padding={false}>NoPad</Container>);
    const el = container.firstChild as HTMLElement;
    expect(el.className).not.toContain('px-4');
  });
});
