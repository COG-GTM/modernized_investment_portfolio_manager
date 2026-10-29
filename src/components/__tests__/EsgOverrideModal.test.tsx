import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import EsgOverrideModal, { validateOverrideForm } from '../EsgOverrideModal';
import { computedMetric, overriddenMetric } from '../../test/esgFixtures';

describe('validateOverrideForm (RP-50)', () => {
  it('requires a reason of at least 10 characters', () => {
    expect(validateOverrideForm('override', '1.2', 'too short').reason).toMatch(/at least 10 characters/);
    expect(validateOverrideForm('override', '1.2', 'long enough reason').reason).toBeUndefined();
    expect(validateOverrideForm('clear', '', 'long enough reason')).toEqual({});
  });

  it('rejects negative and non-numeric values', () => {
    expect(validateOverrideForm('override', '-1', 'long enough reason').value).toMatch(/zero or greater/);
    expect(validateOverrideForm('override', 'abc', 'long enough reason').value).toMatch(/must be a number/);
    expect(validateOverrideForm('override', '', 'long enough reason').value).toMatch(/required/);
    expect(validateOverrideForm('override', '0', 'long enough reason').value).toBeUndefined();
  });
});

describe('EsgOverrideModal (RP-50)', () => {
  it('shows validation errors and does not submit when the reason is too short', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<EsgOverrideModal isOpen mode="override" metric={computedMetric} onSubmit={onSubmit} onCancel={() => {}} />);

    fireEvent.change(screen.getByLabelText(/Override value/), { target: { value: '1.1' } });
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: 'short' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save override' }));

    expect(await screen.findByText(/at least 10 characters/)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('rejects a negative value', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<EsgOverrideModal isOpen mode="override" metric={computedMetric} onSubmit={onSubmit} onCancel={() => {}} />);

    fireEvent.change(screen.getByLabelText(/Override value/), { target: { value: '-5' } });
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: 'A valid reason that is long enough' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save override' }));

    expect(await screen.findByText(/zero or greater/)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('submits value and trimmed reason when valid', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<EsgOverrideModal isOpen mode="override" metric={computedMetric} onSubmit={onSubmit} onCancel={() => {}} />);

    fireEvent.change(screen.getByLabelText(/Override value/), { target: { value: '1.1' } });
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: '  Provider restated MSFT scope 2  ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save override' }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith({ value: 1.1, reason: 'Provider restated MSFT scope 2' }));
  });

  it('clear mode hides the value field and submits a null value', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<EsgOverrideModal isOpen mode="clear" metric={overriddenMetric} onSubmit={onSubmit} onCancel={() => {}} />);

    expect(screen.getByRole('heading', { name: /Clear carbon intensity override/ })).toBeInTheDocument();
    expect(screen.queryByLabelText(/Override value/)).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: 'Restatement withdrawn by provider' } });
    fireEvent.click(screen.getByRole('button', { name: 'Clear override' }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledWith({ value: null, reason: 'Restatement withdrawn by provider' }));
  });

  it('shows server-side validation errors and supports cancel', () => {
    const onCancel = vi.fn();
    render(
      <EsgOverrideModal
        isOpen
        mode="override"
        metric={computedMetric}
        onSubmit={vi.fn()}
        onCancel={onCancel}
        serverError="Reason must be at least 10 characters"
      />
    );

    expect(screen.getByTestId('esg-server-error')).toHaveTextContent('Reason must be at least 10 characters');
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onCancel).toHaveBeenCalled();
  });

  it('renders nothing when closed', () => {
    const { container } = render(<EsgOverrideModal isOpen={false} mode="override" metric={computedMetric} onSubmit={vi.fn()} onCancel={() => {}} />);
    expect(container).toBeEmptyDOMElement();
  });
});
