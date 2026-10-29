/**
 * RP-49: Show carbon intensity on the portfolio dashboard (PortfolioSummary).
 *
 * Expected component contract (see docs/specs/esg-test-matrix.md):
 *   <CarbonIntensityCard metric={EsgMetric | null} loading?={boolean}
 *                        onOverride?={() => void} onViewHistory?={() => void} />
 */
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ComponentType } from 'react';
import {
  AS_OF_MONTH_PATTERN,
  COMPUTED_METRIC,
  EMPTY_METRIC,
  EMPTY_STATE_PATTERN,
  OVERRIDDEN_METRIC,
  OVERRIDE_INDICATOR_PATTERN,
  UNIT_PATTERN,
  loadComponent,
} from './esgTestUtils';

let CarbonIntensityCard: ComponentType<any>;

beforeEach(async () => {
  CarbonIntensityCard = await loadComponent('CarbonIntensityCard', 'RP-49');
});

function card() {
  return screen.getByTestId('carbon-intensity-card');
}

describe('RP-49 CarbonIntensityCard', () => {
  it('RP-49-01 renders the effective value with its unit', () => {
    /** RP-49 AC: effective value with unit. */
    render(<CarbonIntensityCard metric={COMPUTED_METRIC} />);
    expect(within(card()).getByText(/3\.3/)).toBeInTheDocument();
    expect(within(card()).getByText(UNIT_PATTERN)).toBeInTheDocument();
  });

  it('RP-49-02 renders the as-of month', () => {
    /** RP-49 AC: as-of month. */
    render(<CarbonIntensityCard metric={COMPUTED_METRIC} />);
    expect(within(card()).getByText(AS_OF_MONTH_PATTERN)).toBeInTheDocument();
  });

  it('RP-49-03 renders coverage as a percentage', () => {
    /** RP-49 AC: coverage. */
    render(<CarbonIntensityCard metric={COMPUTED_METRIC} />);
    expect(within(card()).getByText(/90(\.0)?\s?%/)).toBeInTheDocument();
    expect(within(card()).getByText(/coverage/i)).toBeInTheDocument();
  });

  it('RP-49-04 shows no override indicator for a computed value', () => {
    /** RP-49 AC: indicator only when the value is an override. */
    render(<CarbonIntensityCard metric={COMPUTED_METRIC} />);
    expect(within(card()).queryByTestId('override-indicator')).not.toBeInTheDocument();
  });

  it('RP-49-05 shows an override indicator and the override value when source is override', () => {
    /** RP-49 AC: an indicator when the value is an override. */
    render(<CarbonIntensityCard metric={OVERRIDDEN_METRIC} />);
    const indicator = within(card()).getByTestId('override-indicator');
    expect(indicator).toHaveTextContent(OVERRIDE_INDICATOR_PATTERN);
    expect(within(card()).getByText(/2\.75/)).toBeInTheDocument();
  });

  it('RP-49-06 keeps the computed value visible next to an override', () => {
    /** RP-49 AC (edge): a portfolio manager can still see what the procedure computed. */
    render(<CarbonIntensityCard metric={OVERRIDDEN_METRIC} />);
    expect(within(card()).getByText(/3\.3/)).toBeInTheDocument();
  });

  it('RP-49-07 renders the empty state when the API returns no metric', () => {
    /** RP-49 AC: empty state when no metric exists (null payload). */
    render(<CarbonIntensityCard metric={null} />);
    expect(within(card()).getByText(EMPTY_STATE_PATTERN)).toBeInTheDocument();
    expect(within(card()).queryByText(UNIT_PATTERN)).not.toBeInTheDocument();
  });

  it('RP-49-08 renders the empty state when the metric has null values', () => {
    /** RP-49 AC (edge): a known account whose metric has not been computed yet. */
    render(<CarbonIntensityCard metric={EMPTY_METRIC} />);
    expect(within(card()).getByText(EMPTY_STATE_PATTERN)).toBeInTheDocument();
    expect(within(card()).queryByTestId('override-indicator')).not.toBeInTheDocument();
  });

  it('RP-49-09 shows a loading state while the metric is being fetched', () => {
    /** RP-49 AC (edge): loading state is neither the value nor the empty state. */
    render(<CarbonIntensityCard metric={null} loading />);
    expect(within(card()).getByRole('status')).toBeInTheDocument();
    expect(within(card()).queryByText(EMPTY_STATE_PATTERN)).not.toBeInTheDocument();
  });

  it('RP-49-10 exposes an Override action that calls onOverride', async () => {
    /** RP-50 AC: UI modal is opened from the dashboard. */
    const onOverride = vi.fn();
    render(<CarbonIntensityCard metric={COMPUTED_METRIC} onOverride={onOverride} />);
    await userEvent.click(within(card()).getByRole('button', { name: /override/i }));
    expect(onOverride).toHaveBeenCalledTimes(1);
  });

  it('RP-49-11 exposes a History action that calls onViewHistory', async () => {
    /** RP-51 AC: dashboard has a history view. */
    const onViewHistory = vi.fn();
    render(<CarbonIntensityCard metric={COMPUTED_METRIC} onViewHistory={onViewHistory} />);
    await userEvent.click(within(card()).getByRole('button', { name: /history/i }));
    expect(onViewHistory).toHaveBeenCalledTimes(1);
  });

  it('RP-49-12 does not offer the Override action in the empty state', () => {
    /** RP-50 AC (edge): nothing to override when no metric exists. */
    render(<CarbonIntensityCard metric={null} onOverride={vi.fn()} />);
    expect(within(card()).queryByRole('button', { name: /override/i })).not.toBeInTheDocument();
  });

  it('RP-49-13 formats a zero effective value as 0, not as the empty state', () => {
    /** RP-49 AC (edge): zero is a valid value. */
    render(<CarbonIntensityCard metric={{ ...COMPUTED_METRIC, computed_value: 0, effective_value: 0 }} />);
    expect(within(card()).queryByText(EMPTY_STATE_PATTERN)).not.toBeInTheDocument();
    expect(within(card()).getByText(/\b0(\.0+)?\b/)).toBeInTheDocument();
  });
});
