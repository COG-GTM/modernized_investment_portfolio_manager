import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Alert, AlertTitle, AlertDescription } from './alert';

describe('ui/Alert components', () => {
  it('renders Alert', () => {
    render(<Alert>Alert content</Alert>);
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Alert content')).toBeInTheDocument();
  });

  it('Alert applies className', () => {
    render(<Alert className="my-alert">Alert</Alert>);
    expect(screen.getByRole('alert')).toHaveClass('my-alert');
  });

  it('Alert default variant', () => {
    render(<Alert>Default</Alert>);
    expect(screen.getByRole('alert')).toHaveClass('bg-card');
  });

  it('Alert destructive variant', () => {
    render(<Alert variant="destructive">Error</Alert>);
    expect(screen.getByRole('alert')).toHaveClass('text-destructive');
  });

  it('renders AlertTitle', () => {
    render(<Alert><AlertTitle className="my-title">Title</AlertTitle></Alert>);
    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(document.querySelector('[data-slot="alert-title"]')).toHaveClass('my-title');
  });

  it('renders AlertDescription', () => {
    render(<Alert><AlertDescription className="my-desc">Desc</AlertDescription></Alert>);
    expect(screen.getByText('Desc')).toBeInTheDocument();
    expect(document.querySelector('[data-slot="alert-description"]')).toHaveClass('my-desc');
  });
});
