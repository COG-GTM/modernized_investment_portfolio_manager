import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import CarbonIntensityTile from './CarbonIntensityTile';
import { computedEsg, overriddenEsg } from '../../test/esgFixtures';

describe('CarbonIntensityTile', () => {
  it('shows the computed value without an override indicator', () => {
    render(<CarbonIntensityTile esg={computedEsg} onOverrideClick={vi.fn()} />);

    expect(screen.getByTestId('esg-effective-value')).toHaveTextContent('64.14');
    expect(screen.queryByTestId('esg-override-indicator')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Override value' })).toBeInTheDocument();
  });

  it('shows the override indicator, effective value and reason after an override', () => {
    render(<CarbonIntensityTile esg={overriddenEsg} onOverrideClick={vi.fn()} />);

    expect(screen.getByTestId('esg-override-indicator')).toHaveTextContent('Overridden');
    expect(screen.getByTestId('esg-effective-value')).toHaveTextContent('70.00');
    expect(screen.getByTestId('esg-override-details')).toHaveTextContent('Computed value: 64.14');
    expect(screen.getByTestId('esg-override-details')).toHaveTextContent(overriddenEsg.override!.reason);
    expect(screen.getByRole('button', { name: 'Change override' })).toBeInTheDocument();
  });

  it('hides the override action when there is no metric', () => {
    render(<CarbonIntensityTile esg={{ ...computedEsg, hasMetric: false, source: 'none' }} onOverrideClick={vi.fn()} />);

    expect(screen.getByText('No carbon intensity data for this portfolio yet.')).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
