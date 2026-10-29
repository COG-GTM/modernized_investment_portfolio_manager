/**
 * RP-50: Override with a reason (UI modal from the dashboard).
 *
 * Expected component contract (see docs/specs/esg-test-matrix.md):
 *   <OverrideModal isOpen={boolean} asOfMonth={string} currentValue={number | null}
 *                  onSubmit={(value: number, reason: string) => void | Promise<void>}
 *                  onClose={() => void} serverError?={string | null} submitting?={boolean} />
 * Fields are labelled "Value" and "Reason"; the confirm button is named "Save override".
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ComponentType } from 'react';
import { loadComponent } from './esgTestUtils';

let OverrideModal: ComponentType<any>;

beforeEach(async () => {
  OverrideModal = await loadComponent('OverrideModal', 'RP-50');
});

const VALID_REASON = 'Issuer restated scope 2 figures';

function renderModal(overrides: Record<string, unknown> = {}) {
  const props = {
    isOpen: true,
    asOfMonth: '2026-10',
    currentValue: 3.3,
    onSubmit: vi.fn(),
    onClose: vi.fn(),
    ...overrides,
  };
  render(<OverrideModal {...props} />);
  return props;
}

function valueInput() {
  return screen.getByLabelText(/value/i);
}

function reasonInput() {
  return screen.getByLabelText(/reason/i);
}

function saveButton() {
  return screen.getByRole('button', { name: /save override/i });
}

async function fill(value: string, reason: string) {
  await userEvent.clear(valueInput());
  if (value !== '') {
    await userEvent.type(valueInput(), value);
  }
  await userEvent.clear(reasonInput());
  if (reason !== '') {
    await userEvent.type(reasonInput(), reason);
  }
}

describe('RP-50 OverrideModal', () => {
  it('RP-50-01 renders as a dialog with value and reason fields when open', () => {
    /** RP-50 AC: UI modal from the dashboard. */
    renderModal();
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(valueInput()).toBeInTheDocument();
    expect(reasonInput()).toBeInTheDocument();
    expect(saveButton()).toBeInTheDocument();
  });

  it('RP-50-02 renders nothing when closed', () => {
    renderModal({ isOpen: false });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('RP-50-03 shows the as-of month the override applies to', () => {
    /** RP-50 AC: applies to the current as-of month only. */
    renderModal();
    expect(screen.getByRole('dialog')).toHaveTextContent(/2026-10|Oct(ober)?\s+2026/i);
  });

  it('RP-50-04 submits value and reason when both are valid', async () => {
    /** RP-50 AC: PUT with value and reason. */
    const { onSubmit } = renderModal();
    await fill('2.75', VALID_REASON);
    await userEvent.click(saveButton());
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(2.75, VALID_REASON);
  });

  it('RP-50-05 rejects an empty reason', async () => {
    /** RP-50 AC: reason mandatory. */
    const { onSubmit } = renderModal();
    await fill('2.75', '');
    await userEvent.click(saveButton());
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText(/reason/i, { selector: '[role="alert"], [id$="-error"], .text-destructive, .text-red-600' })).toBeInTheDocument();
  });

  it('RP-50-06 rejects a reason shorter than 10 characters', async () => {
    /** RP-50 AC: reason minimum 10 characters. */
    const { onSubmit } = renderModal();
    await fill('2.75', 'too short');
    await userEvent.click(saveButton());
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText(/at least 10 characters/i)).toBeInTheDocument();
  });

  it('RP-50-07 accepts a reason of exactly 10 characters', async () => {
    /** RP-50 AC (boundary). */
    const { onSubmit } = renderModal();
    await fill('2.75', '1234567890');
    await userEvent.click(saveButton());
    expect(onSubmit).toHaveBeenCalledWith(2.75, '1234567890');
  });

  it('RP-50-08 rejects a negative value', async () => {
    /** RP-50 AC: value non-negative. */
    const { onSubmit } = renderModal();
    await fill('-1', VALID_REASON);
    await userEvent.click(saveButton());
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText(/(non-negative|cannot be negative|0 or (greater|more)|greater than or equal to 0)/i)).toBeInTheDocument();
  });

  it('RP-50-09 accepts zero as a value', async () => {
    /** RP-50 AC (boundary): zero is non-negative. */
    const { onSubmit } = renderModal();
    await fill('0', VALID_REASON);
    await userEvent.click(saveButton());
    expect(onSubmit).toHaveBeenCalledWith(0, VALID_REASON);
  });

  it('RP-50-10 rejects an empty or non-numeric value', async () => {
    /** RP-50 AC (edge): value is required and numeric. */
    const { onSubmit } = renderModal();
    await fill('', VALID_REASON);
    await userEvent.click(saveButton());
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText(/value/i, { selector: '[role="alert"], [id$="-error"], .text-destructive, .text-red-600' })).toBeInTheDocument();
  });

  it('RP-50-11 shows the server validation error returned by the API', () => {
    /** RP-50 AC: validation errors returned and shown. */
    renderModal({ serverError: 'reason must be at least 10 characters' });
    expect(screen.getByRole('alert')).toHaveTextContent(/reason must be at least 10 characters/i);
  });

  it('RP-50-12 shows the current computed value for context', () => {
    /** RP-50 AC (edge): the manager sees what they are overriding. */
    renderModal({ currentValue: 3.3 });
    expect(screen.getByRole('dialog')).toHaveTextContent(/3\.3/);
  });

  it('RP-50-13 calls onClose from the cancel button', async () => {
    const { onClose, onSubmit } = renderModal();
    await userEvent.click(screen.getByRole('button', { name: /cancel/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('RP-50-14 calls onClose on Escape', async () => {
    const { onClose } = renderModal();
    await userEvent.keyboard('{Escape}');
    expect(onClose).toHaveBeenCalled();
  });

  it('RP-50-15 disables the save button while submitting', () => {
    /** RP-50 AC (edge): no double submit. */
    renderModal({ submitting: true });
    expect(saveButton()).toBeDisabled();
  });

  it('RP-50-16 trims whitespace before checking the reason length', async () => {
    /** RP-50 AC (edge): padding does not satisfy the minimum. */
    const { onSubmit } = renderModal();
    await fill('2.75', '   short   ');
    await userEvent.click(saveButton());
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
