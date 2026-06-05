import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Card from './Card';

describe('Card', () => {
  it('renders children', () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<Card className="my-class">Content</Card>);
    expect(container.firstChild).toHaveClass('my-class');
  });

  it('applies hover styles when hover prop is true', () => {
    const { container } = render(<Card hover>Hover card</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('hover:shadow-lg');
  });

  it('does not apply hover styles by default', () => {
    const { container } = render(<Card>Card</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).not.toContain('hover:shadow-lg');
  });

  it('applies md padding by default', () => {
    const { container } = render(<Card>Padded</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('p-6');
  });

  it('applies sm padding variant', () => {
    const { container } = render(<Card padding="sm">Small pad</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('p-4');
  });

  it('applies lg padding variant', () => {
    const { container } = render(<Card padding="lg">Large pad</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('p-8');
  });

  it('has border and shadow', () => {
    const { container } = render(<Card>Content</Card>);
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('border');
    expect(card.className).toContain('shadow-sm');
  });
});
