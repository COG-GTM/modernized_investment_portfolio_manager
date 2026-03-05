import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ErrorBoundary from '../components/ErrorBoundary';

function ProblemChild(): JSX.Element {
  throw new Error('Test error');
}

function GoodChild(): JSX.Element {
  return <div>All good</div>;
}

describe('ErrorBoundary', () => {
  it('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <GoodChild />
      </ErrorBoundary>
    );
    expect(screen.getByText('All good')).toBeInTheDocument();
  });

  it('renders error UI when a child throws', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ProblemChild />
      </ErrorBoundary>
    );

    expect(screen.getByText('System Error')).toBeInTheDocument();
    expect(screen.getByText('An unexpected error has occurred')).toBeInTheDocument();
    expect(screen.getByText('Test error')).toBeInTheDocument();
    expect(screen.getByText('Press to Continue')).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  it('recovers when reset button is clicked', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    let shouldThrow = true;

    function ConditionalChild(): JSX.Element {
      if (shouldThrow) {
        throw new Error('Conditional error');
      }
      return <div>Recovered</div>;
    }

    render(
      <ErrorBoundary>
        <ConditionalChild />
      </ErrorBoundary>
    );

    expect(screen.getByText('System Error')).toBeInTheDocument();

    shouldThrow = false;
    fireEvent.click(screen.getByText('Press to Continue'));

    expect(screen.getByText('Recovered')).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  it('renders custom fallback when provided', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary fallback={<div>Custom fallback</div>}>
        <ProblemChild />
      </ErrorBoundary>
    );

    expect(screen.getByText('Custom fallback')).toBeInTheDocument();

    consoleSpy.mockRestore();
  });
});
