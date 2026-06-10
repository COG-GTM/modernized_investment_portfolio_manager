import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ConfirmationDialog from '../../../components/dialogs/ConfirmationDialog';

const defaultProps = {
  isOpen: true,
  title: 'Confirm Exit',
  message: 'Are you sure you want to exit?',
  onConfirm: vi.fn(),
  onCancel: vi.fn(),
};

describe('ConfirmationDialog', () => {
  it('renders when open', () => {
    render(<ConfirmationDialog {...defaultProps} />);
    expect(screen.getByText('Confirm Exit')).toBeInTheDocument();
    expect(screen.getByText('Are you sure you want to exit?')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(<ConfirmationDialog {...defaultProps} isOpen={false} />);
    expect(screen.queryByText('Confirm Exit')).not.toBeInTheDocument();
  });

  it('calls onCancel when Cancel clicked', () => {
    const onCancel = vi.fn();
    render(<ConfirmationDialog {...defaultProps} onCancel={onCancel} />);
    fireEvent.click(screen.getByText('Cancel'));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('calls onConfirm when Exit Application clicked', () => {
    const onConfirm = vi.fn();
    render(<ConfirmationDialog {...defaultProps} onConfirm={onConfirm} />);
    fireEvent.click(screen.getByText('Exit Application'));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('calls onCancel on Escape key', () => {
    const onCancel = vi.fn();
    render(<ConfirmationDialog {...defaultProps} onCancel={onCancel} />);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('has dialog role', () => {
    render(<ConfirmationDialog {...defaultProps} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('has aria-modal attribute', () => {
    render(<ConfirmationDialog {...defaultProps} />);
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
  });

  it('applies custom className', () => {
    render(<ConfirmationDialog {...defaultProps} className="custom" />);
    const dialog = screen.getByRole('dialog');
    const card = dialog.firstChild as HTMLElement;
    expect(card.className).toContain('custom');
  });
});
