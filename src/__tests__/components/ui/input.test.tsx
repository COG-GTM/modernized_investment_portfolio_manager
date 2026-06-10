import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Input } from '../../../components/ui/input';

describe('Input', () => {
  it('renders an input element', () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
  });

  it('applies type prop', () => {
    render(<Input type="password" data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveAttribute('type', 'password');
  });

  it('handles onChange', () => {
    const onChange = vi.fn();
    render(<Input onChange={onChange} data-testid="input" />);
    fireEvent.change(screen.getByTestId('input'), { target: { value: 'test' } });
    expect(onChange).toHaveBeenCalled();
  });

  it('applies custom className', () => {
    render(<Input className="custom" data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveClass('custom');
  });

  it('forwards ref', () => {
    const ref = { current: null as HTMLInputElement | null };
    render(<Input ref={ref} data-testid="input" />);
    expect(ref.current).toBeInstanceOf(HTMLInputElement);
  });
});
