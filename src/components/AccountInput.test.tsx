import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { AccountInput } from './AccountInput';

vi.mock('./ui/input', () => ({
  Input: React.forwardRef<HTMLInputElement, React.ComponentProps<'input'>>(
    (props, ref) => <input ref={ref} {...props} />
  ),
}));

function Wrapper({ children, defaultError }: { children: React.ReactNode; defaultError?: string }) {
  const methods = useForm({
    defaultValues: { accountNumber: '' },
  });

  React.useEffect(() => {
    if (defaultError) {
      methods.setError('accountNumber', { message: defaultError });
    }
  }, [defaultError, methods]);

  return <FormProvider {...methods}><form>{children}</form></FormProvider>;
}

describe('AccountInput', () => {
  it('renders input field', () => {
    render(
      <Wrapper>
        <AccountInput />
      </Wrapper>
    );
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('renders label', () => {
    render(
      <Wrapper>
        <AccountInput />
      </Wrapper>
    );
    expect(screen.getByText('Account Number')).toBeInTheDocument();
  });

  it('has maxLength 10', () => {
    render(
      <Wrapper>
        <AccountInput />
      </Wrapper>
    );
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('maxLength', '10');
  });

  it('has placeholder text', () => {
    render(
      <Wrapper>
        <AccountInput />
      </Wrapper>
    );
    const input = screen.getByRole('textbox');
    expect(input).toHaveAttribute('placeholder', 'Enter 10-digit account number');
  });

  it('shows error message when present', async () => {
    render(
      <Wrapper defaultError="Invalid account">
        <AccountInput />
      </Wrapper>
    );
    await waitFor(() => {
      expect(screen.getByText('Invalid account')).toBeInTheDocument();
    });
  });

  it('error has alert role', async () => {
    render(
      <Wrapper defaultError="Bad number">
        <AccountInput />
      </Wrapper>
    );
    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });
});
