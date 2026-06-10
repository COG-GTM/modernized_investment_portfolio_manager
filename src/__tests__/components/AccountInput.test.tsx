import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FormProvider, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { AccountInput } from '../../components/AccountInput';
import { accountFormSchema, type AccountFormData } from '../../types/account';

function Wrapper({ children, defaultValues = { accountNumber: '' } }: { children: React.ReactNode; defaultValues?: AccountFormData }) {
  const methods = useForm<AccountFormData>({
    resolver: zodResolver(accountFormSchema),
    mode: 'onChange',
    defaultValues,
  });
  return <FormProvider {...methods}>{children}</FormProvider>;
}

describe('AccountInput', () => {
  it('renders label', () => {
    render(
      <Wrapper>
        <AccountInput />
      </Wrapper>
    );
    expect(screen.getByLabelText('Account Number')).toBeInTheDocument();
  });

  it('renders placeholder', () => {
    render(
      <Wrapper>
        <AccountInput />
      </Wrapper>
    );
    expect(screen.getByPlaceholderText('Enter 10-digit account number')).toBeInTheDocument();
  });

  it('accepts input', () => {
    render(
      <Wrapper>
        <AccountInput />
      </Wrapper>
    );
    const input = screen.getByLabelText('Account Number');
    fireEvent.change(input, { target: { value: '1234567890' } });
    expect(input).toHaveValue('1234567890');
  });

  it('has maxLength 10', () => {
    render(
      <Wrapper>
        <AccountInput />
      </Wrapper>
    );
    expect(screen.getByLabelText('Account Number')).toHaveAttribute('maxLength', '10');
  });

  it('applies custom className', () => {
    render(
      <Wrapper>
        <AccountInput className="my-class" />
      </Wrapper>
    );
    const input = screen.getByLabelText('Account Number');
    expect(input.className).toContain('my-class');
  });
});
