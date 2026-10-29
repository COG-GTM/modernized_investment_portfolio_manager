import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import EsgAuditHistory from '../EsgAuditHistory';
import { auditEntries } from '../../test/esgFixtures';

describe('EsgAuditHistory (RP-51)', () => {
  it('lists audit entries newest first with action, values, who and reason', () => {
    render(<EsgAuditHistory isOpen entries={auditEntries} onClose={() => {}} />);

    const rows = within(screen.getByTestId('esg-history-table')).getAllByRole('row').slice(1);
    expect(rows).toHaveLength(2);
    expect(rows[0]).toHaveTextContent('Clear');
    expect(rows[0]).toHaveTextContent('Restatement withdrawn by provider');
    expect(rows[1]).toHaveTextContent('Override');
    expect(rows[1]).toHaveTextContent('1.10');
    expect(rows[1]).toHaveTextContent('pm_jane');
    expect(rows[1]).toHaveTextContent('Provider restated MSFT scope 2 for 2026-10');
  });

  it('shows an empty state when there is no history', () => {
    render(<EsgAuditHistory isOpen entries={[]} onClose={() => {}} />);
    expect(screen.getByTestId('esg-history-empty')).toBeInTheDocument();
  });

  it('shows loading and error states', () => {
    const { rerender } = render(<EsgAuditHistory isOpen entries={[]} loading onClose={() => {}} />);
    expect(screen.getByRole('status')).toHaveTextContent('Loading history');

    rerender(<EsgAuditHistory isOpen entries={[]} error="Account not found" onClose={() => {}} />);
    expect(screen.getByRole('alert')).toHaveTextContent('Account not found');
  });
});
