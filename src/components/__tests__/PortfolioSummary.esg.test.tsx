import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import PortfolioSummary from '../PortfolioSummary';
import { computedMetric, overriddenMetric } from '../../test/esgFixtures';
import type { Portfolio } from '../../types';

const portfolio: Portfolio = {
  id: 'PF-12345',
  accountNumber: '1234567890',
  name: 'Growth Portfolio',
  totalValue: 100000,
  totalGainLoss: 5000,
  totalGainLossPercent: 5,
  positions: [],
  lastUpdated: '2026-10-29T00:00:00Z',
} as unknown as Portfolio;

describe('PortfolioSummary carbon intensity panel (RP-49)', () => {
  it('omits the panel when no esg props are supplied', () => {
    render(<PortfolioSummary portfolio={portfolio} />);
    expect(screen.queryByTestId('carbon-intensity-card')).not.toBeInTheDocument();
  });

  it('renders the computed state inside the summary', () => {
    render(<PortfolioSummary portfolio={portfolio} esg={{ metric: computedMetric }} />);
    expect(screen.getByTestId('carbon-intensity-card')).toBeInTheDocument();
    expect(screen.getByTestId('carbon-intensity-value')).toHaveTextContent('1.31');
    expect(screen.queryByTestId('override-indicator')).not.toBeInTheDocument();
  });

  it('renders the override indicator inside the summary', () => {
    render(<PortfolioSummary portfolio={portfolio} esg={{ metric: overriddenMetric }} />);
    expect(screen.getByTestId('override-indicator')).toBeInTheDocument();
  });

  it('renders the empty state inside the summary', () => {
    render(<PortfolioSummary portfolio={portfolio} esg={{ metric: null }} />);
    expect(screen.getByTestId('carbon-intensity-empty')).toBeInTheDocument();
  });
});
