import { describe, it, expect } from 'vitest';
import { accountNumberSchema, accountFormSchema } from '../../types/account';

describe('accountNumberSchema', () => {
  it('accepts valid 10-digit account number', () => {
    const result = accountNumberSchema.safeParse('1234567890');
    expect(result.success).toBe(true);
  });

  it('rejects account number shorter than 10 digits', () => {
    const result = accountNumberSchema.safeParse('123456789');
    expect(result.success).toBe(false);
  });

  it('rejects account number longer than 10 digits', () => {
    const result = accountNumberSchema.safeParse('12345678901');
    expect(result.success).toBe(false);
  });

  it('rejects non-numeric characters', () => {
    const result = accountNumberSchema.safeParse('123456789a');
    expect(result.success).toBe(false);
  });

  it('rejects empty string', () => {
    const result = accountNumberSchema.safeParse('');
    expect(result.success).toBe(false);
  });

  it('rejects account number with spaces', () => {
    const result = accountNumberSchema.safeParse('1234 56789');
    expect(result.success).toBe(false);
  });

  it('rejects account number with special characters', () => {
    const result = accountNumberSchema.safeParse('123-456-78');
    expect(result.success).toBe(false);
  });

  it('accepts all zeros (schema only validates format)', () => {
    const result = accountNumberSchema.safeParse('0000000000');
    expect(result.success).toBe(true);
  });
});

describe('accountFormSchema', () => {
  it('validates a complete form with valid account number', () => {
    const result = accountFormSchema.safeParse({ accountNumber: '1234567890' });
    expect(result.success).toBe(true);
  });

  it('rejects form with invalid account number', () => {
    const result = accountFormSchema.safeParse({ accountNumber: 'bad' });
    expect(result.success).toBe(false);
  });

  it('rejects form with missing account number', () => {
    const result = accountFormSchema.safeParse({});
    expect(result.success).toBe(false);
  });

  it('rejects form with non-string account number', () => {
    const result = accountFormSchema.safeParse({ accountNumber: 1234567890 });
    expect(result.success).toBe(false);
  });
});
