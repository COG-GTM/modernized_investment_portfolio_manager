import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import EsgOverrideDialog from './EsgOverrideDialog';
import { computedEsg, jsonResponse, overriddenEsg } from '../../test/esgFixtures';

const REASON = 'Provider revenue for TSLA restated; aligned to Q3 filing.';

function renderDialog(onSaved = vi.fn(), onClose = vi.fn()) {
  render(<EsgOverrideDialog isOpen esg={computedEsg} onClose={onClose} onSaved={onSaved} />);
  return {
    user: userEvent.setup(),
    value: screen.getByLabelText(/Override value/),
    reason: screen.getByLabelText('Reason'),
    submit: screen.getByRole('button', { name: 'Save override' }),
    onSaved,
    onClose,
  };
}

afterEach(() => vi.unstubAllGlobals());

describe('EsgOverrideDialog', () => {
  it('states that the override applies to the current as-of month only', () => {
    renderDialog();
    expect(screen.getByRole('dialog')).toHaveTextContent('current as-of month (2026-11) only');
  });

  it('keeps submit disabled and shows errors until value and reason are valid', async () => {
    const { user, value, reason, submit } = renderDialog();
    expect(submit).toBeDisabled();

    await user.type(value, '-5');
    expect(screen.getByText('Value must be non-negative')).toBeInTheDocument();
    expect(value).toHaveAttribute('aria-invalid', 'true');

    await user.type(reason, 'too short');
    expect(screen.getByText('Reason must be at least 10 characters')).toBeInTheDocument();
    expect(submit).toBeDisabled();

    await user.clear(value);
    await user.type(value, '70');
    await user.clear(reason);
    await user.type(reason, REASON);
    expect(screen.queryByText('Value must be non-negative')).not.toBeInTheDocument();
    expect(screen.queryByText('Reason must be at least 10 characters')).not.toBeInTheDocument();
    expect(submit).toBeEnabled();
  });

  it('submits and hands the updated metric back on success', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, overriddenEsg));
    vi.stubGlobal('fetch', fetchMock);
    const { user, value, reason, submit, onSaved } = renderDialog();

    await user.type(value, '70');
    await user.type(reason, `  ${REASON}  `);
    await user.click(submit);

    await waitFor(() => expect(onSaved).toHaveBeenCalledWith(overriddenEsg));
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ value: 70, reason: REASON });
  });

  it('shows server-side validation errors inline', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(422, {
      detail: [{ loc: ['body', 'reason'], msg: 'Value error, Reason must be at most 1000 characters' }],
    })));
    const { user, value, reason, submit, onSaved } = renderDialog();

    await user.type(value, '70');
    await user.type(reason, REASON);
    await user.click(submit);

    expect(await screen.findByText('Reason must be at most 1000 characters')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('Please correct the highlighted fields.');
    expect(reason).toHaveAttribute('aria-invalid', 'true');
    expect(onSaved).not.toHaveBeenCalled();
  });

  it('shows non-field errors such as the no-metric conflict', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(409, { detail: 'No ESG metric exists for this account yet' })));
    const { user, value, reason, submit } = renderDialog();

    await user.type(value, '70');
    await user.type(reason, REASON);
    await user.click(submit);

    expect(await screen.findByRole('alert')).toHaveTextContent('No ESG metric exists for this account yet');
  });

  it('closes on Escape and Cancel', async () => {
    const { user, onClose } = renderDialog();
    await user.keyboard('{Escape}');
    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onClose).toHaveBeenCalledTimes(2);
  });
});
