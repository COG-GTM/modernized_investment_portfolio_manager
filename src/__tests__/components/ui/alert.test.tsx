import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Alert, AlertTitle, AlertDescription } from '../../../components/ui/alert';

describe('Alert', () => {
  it('renders children', () => {
    render(<Alert>Alert message</Alert>);
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Alert message')).toBeInTheDocument();
  });

  it('applies default variant', () => {
    render(<Alert>Default</Alert>);
    expect(screen.getByRole('alert')).toHaveClass('bg-card');
  });

  it('applies destructive variant', () => {
    render(<Alert variant="destructive">Error</Alert>);
    expect(screen.getByRole('alert')).toHaveClass('text-destructive');
  });

  it('applies custom className', () => {
    render(<Alert className="custom">Msg</Alert>);
    expect(screen.getByRole('alert')).toHaveClass('custom');
  });
});

describe('AlertTitle', () => {
  it('renders', () => {
    render(<AlertTitle>Title</AlertTitle>);
    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(screen.getByText('Title')).toHaveClass('font-medium');
  });
});

describe('AlertDescription', () => {
  it('renders', () => {
    render(<AlertDescription>Description</AlertDescription>);
    expect(screen.getByText('Description')).toBeInTheDocument();
    expect(screen.getByText('Description')).toHaveClass('text-sm');
  });
});
