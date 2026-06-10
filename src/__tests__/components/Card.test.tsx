import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Card from '../../components/Card';

describe('Card', () => {
  it('renders children', () => {
    render(<Card>Content</Card>);
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('applies hover classes when hover is true', () => {
    const { container } = render(<Card hover>Hover</Card>);
    expect(container.firstChild).toHaveClass('hover:shadow-lg');
  });

  it('does not apply hover classes by default', () => {
    const { container } = render(<Card>No hover</Card>);
    const el = container.firstChild as HTMLElement;
    expect(el.className).not.toContain('hover:shadow-lg');
  });

  it('applies sm padding', () => {
    const { container } = render(<Card padding="sm">Small</Card>);
    expect(container.firstChild).toHaveClass('p-4');
  });

  it('applies md padding by default', () => {
    const { container } = render(<Card>Medium</Card>);
    expect(container.firstChild).toHaveClass('p-6');
  });

  it('applies lg padding', () => {
    const { container } = render(<Card padding="lg">Large</Card>);
    expect(container.firstChild).toHaveClass('p-8');
  });

  it('applies custom className', () => {
    const { container } = render(<Card className="my-class">X</Card>);
    expect(container.firstChild).toHaveClass('my-class');
  });

  it('applies custom style', () => {
    const { container } = render(<Card style={{ color: 'red' }}>X</Card>);
    expect((container.firstChild as HTMLElement).style.color).toBe('red');
  });
});
