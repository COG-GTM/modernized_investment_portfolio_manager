import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import CarbonIntensityCard from '../CarbonIntensityCard';
import { computedMetric, overriddenMetric } from '../../test/esgFixtures';

describe('CarbonIntensityCard (RP-49)', () => {
  it('renders the computed value, unit, as-of month and coverage', () => {
    render(<CarbonIntensityCard metric={computedMetric} />);

    expect(screen.getByTestId('carbon-intensity-value')).toHaveTextContent('1.31');
    expect(screen.getByTestId('carbon-intensity-value')).toHaveTextContent('tCO2e per $M revenue');
    expect(screen.getByText(/As of October 2026/)).toBeInTheDocument();
    expect(screen.getByTestId('carbon-intensity-coverage')).toHaveTextContent('60.8% of market value');
    expect(screen.getByText('computed')).toBeInTheDocument();
    expect(screen.queryByTestId('override-indicator')).not.toBeInTheDocument();
  });

  it('renders the empty state when no metric exists', () => {
    render(<CarbonIntensityCard metric={null} />);

    expect(screen.getByTestId('carbon-intensity-empty')).toBeInTheDocument();
    expect(screen.getByText('Not available')).toBeInTheDocument();
    expect(screen.queryByTestId('carbon-intensity-value')).not.toBeInTheDocument();
  });

  it('shows the override indicator and override details when the value is an override', () => {
    render(<CarbonIntensityCard metric={overriddenMetric} onOverride={() => {}} onClearOverride={() => {}} />);

    expect(screen.getByTestId('override-indicator')).toHaveTextContent('Override');
    expect(screen.getByTestId('carbon-intensity-value')).toHaveTextContent('1.10');
    expect(screen.getByTestId('override-detail')).toHaveTextContent('pm_jane');
    expect(screen.getByTestId('override-detail')).toHaveTextContent('Provider restated MSFT scope 2');
    expect(screen.getByRole('button', { name: 'Clear override' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Change override' })).toBeInTheDocument();
  });

  it('shows loading and error states', () => {
    const { rerender } = render(<CarbonIntensityCard metric={null} loading />);
    expect(screen.getByRole('status')).toHaveTextContent('Loading carbon intensity');

    rerender(<CarbonIntensityCard metric={null} error="Unable to connect to the server." />);
    expect(screen.getByRole('alert')).toHaveTextContent('Unable to connect to the server.');
  });

  it('invokes the override and history callbacks', () => {
    const onOverride = vi.fn();
    const onViewHistory = vi.fn();
    render(<CarbonIntensityCard metric={computedMetric} onOverride={onOverride} onViewHistory={onViewHistory} />);

    fireEvent.click(screen.getByRole('button', { name: 'Override value' }));
    fireEvent.click(screen.getByRole('button', { name: 'View history' }));

    expect(onOverride).toHaveBeenCalledTimes(1);
    expect(onViewHistory).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('button', { name: 'Clear override' })).not.toBeInTheDocument();
  });
});
