import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ConfirmationDialog from './ConfirmationDialog';

vi.mock('../../utils/accessibility', () => ({
  trapFocus: vi.fn(() => vi.fn()),
}));

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

  it('renders Cancel button', () => {
    render(<ConfirmationDialog {...defaultProps} />);
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });

  it('renders Exit Application button', () => {
    render(<ConfirmationDialog {...defaultProps} />);
    expect(screen.getByText('Exit Application')).toBeInTheDocument();
  });

  it('calls onCancel when Cancel clicked', () => {
    const onCancel = vi.fn();
    render(<ConfirmationDialog {...defaultProps} onCancel={onCancel} />);
    fireEvent.click(screen.getByText('Cancel'));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it('calls onConfirm when Exit Application clicked', () => {
    const onConfirm = vi.fn();
    render(<ConfirmationDialog {...defaultProps} onConfirm={onConfirm} />);
    fireEvent.click(screen.getByText('Exit Application'));
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it('calls onCancel on Escape key', () => {
    const onCancel = vi.fn();
    render(<ConfirmationDialog {...defaultProps} onCancel={onCancel} />);
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it('has dialog role', () => {
    render(<ConfirmationDialog {...defaultProps} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('has aria-modal', () => {
    render(<ConfirmationDialog {...defaultProps} />);
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
  });

  it('applies custom className', () => {
    const { container } = render(
      <ConfirmationDialog {...defaultProps} className="my-dialog" />
    );
    expect(container.innerHTML).toContain('my-dialog');
  });
});
