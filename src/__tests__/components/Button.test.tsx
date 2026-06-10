import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Button from '../../components/Button';

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick handler', () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Click</Button>);
    fireEvent.click(screen.getByText('Click'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('applies primary variant by default', () => {
    render(<Button>Primary</Button>);
    const btn = screen.getByText('Primary');
    expect(btn.className).toContain('bg-primary');
  });

  it('applies secondary variant', () => {
    render(<Button variant="secondary">Secondary</Button>);
    const btn = screen.getByText('Secondary');
    expect(btn.className).toContain('bg-secondary');
  });

  it('applies outline variant', () => {
    render(<Button variant="outline">Outline</Button>);
    const btn = screen.getByText('Outline');
    expect(btn.className).toContain('border');
  });

  it('applies ghost variant', () => {
    render(<Button variant="ghost">Ghost</Button>);
    const btn = screen.getByText('Ghost');
    expect(btn.className).toContain('hover:bg-accent');
  });

  it('applies size sm', () => {
    render(<Button size="sm">Small</Button>);
    const btn = screen.getByText('Small');
    expect(btn.className).toContain('px-3');
  });

  it('applies size lg', () => {
    render(<Button size="lg">Large</Button>);
    const btn = screen.getByText('Large');
    expect(btn.className).toContain('px-6');
  });

  it('is disabled when disabled prop set', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByText('Disabled')).toBeDisabled();
  });

  it('applies custom className', () => {
    render(<Button className="custom-class">Btn</Button>);
    expect(screen.getByText('Btn').className).toContain('custom-class');
  });
});
