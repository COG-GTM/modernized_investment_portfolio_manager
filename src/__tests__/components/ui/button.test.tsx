import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../../../components/ui/button';

describe('Button (UI)', () => {
  it('renders children', () => {
    render(<Button>Click</Button>);
    expect(screen.getByText('Click')).toBeInTheDocument();
  });

  it('applies default variant', () => {
    render(<Button>Btn</Button>);
    expect(screen.getByText('Btn')).toHaveClass('bg-primary');
  });

  it('applies destructive variant', () => {
    render(<Button variant="destructive">Del</Button>);
    expect(screen.getByText('Del')).toHaveClass('bg-destructive');
  });

  it('applies outline variant', () => {
    render(<Button variant="outline">Out</Button>);
    expect(screen.getByText('Out')).toHaveClass('border');
  });

  it('applies secondary variant', () => {
    render(<Button variant="secondary">Sec</Button>);
    expect(screen.getByText('Sec')).toHaveClass('bg-secondary');
  });

  it('applies ghost variant', () => {
    render(<Button variant="ghost">Ghost</Button>);
    expect(screen.getByText('Ghost')).toHaveClass('hover:bg-accent');
  });

  it('applies sm size', () => {
    render(<Button size="sm">S</Button>);
    expect(screen.getByText('S')).toHaveClass('h-8');
  });

  it('applies lg size', () => {
    render(<Button size="lg">L</Button>);
    expect(screen.getByText('L')).toHaveClass('h-10');
  });

  it('handles onClick', () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Btn</Button>);
    fireEvent.click(screen.getByText('Btn'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop set', () => {
    render(<Button disabled>Btn</Button>);
    expect(screen.getByText('Btn')).toBeDisabled();
  });

  it('applies custom className', () => {
    render(<Button className="my-class">Btn</Button>);
    expect(screen.getByText('Btn')).toHaveClass('my-class');
  });
});
