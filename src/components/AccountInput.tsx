import { useEffect } from 'react';
import { useFormContext } from 'react-hook-form';
import { Input } from './ui/input';
import { cn } from '../lib/utils';
import type { AccountFormData } from '../types/account';

interface AccountInputProps {
  className?: string;
  autoFocus?: boolean;
}

export function AccountInput({ className, autoFocus = true }: AccountInputProps) {
  const {
    register,
    formState: { errors },
    setFocus,
  } = useFormContext<AccountFormData>();

  useEffect(() => {
    if (autoFocus) {
      setFocus('accountNumber');
    }
  }, [autoFocus, setFocus]);

  return (
    <div className="space-y-2">
      <label htmlFor="accountNumber" className="text-sm font-medium">
        Account Number
      </label>
      <Input
        id="accountNumber"
        type="text"
        placeholder="Enter 9-digit account number"
        maxLength={9}
        className={cn(
          errors.accountNumber && 'border-destructive focus-visible:border-destructive',
          className
        )}
        {...register('accountNumber')}
      />
      {errors.accountNumber && (
        <p className="text-sm text-destructive" role="alert">
          {errors.accountNumber.message}
        </p>
      )}
    </div>
  );
}
