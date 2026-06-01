import { describe, it, expect } from 'vitest';
import { accountNumberSchema, accountFormSchema } from '../account';

describe('accountNumberSchema', () => {
  it('accepts a valid 10-digit account number', () => {
    const result = accountNumberSchema.safeParse('1234567890');
    expect(result.success).toBe(true);
  });

  it('rejects a number shorter than 10 digits', () => {
    const result = accountNumberSchema.safeParse('12345');
    expect(result.success).toBe(false);
  });

  it('rejects a number longer than 10 digits', () => {
    const result = accountNumberSchema.safeParse('12345678901');
    expect(result.success).toBe(false);
  });

  it('rejects non-numeric characters', () => {
    const result = accountNumberSchema.safeParse('123456789a');
    expect(result.success).toBe(false);
  });

  it('rejects an empty string', () => {
    const result = accountNumberSchema.safeParse('');
    expect(result.success).toBe(false);
  });

  it('rejects strings with spaces', () => {
    const result = accountNumberSchema.safeParse('1234 67890');
    expect(result.success).toBe(false);
  });

  it('rejects strings with special characters', () => {
    const result = accountNumberSchema.safeParse('123-456-78');
    expect(result.success).toBe(false);
  });

  it('accepts all zeros', () => {
    const result = accountNumberSchema.safeParse('0000000000');
    expect(result.success).toBe(true);
  });
});

describe('accountFormSchema', () => {
  it('accepts a valid form with 10-digit account number', () => {
    const result = accountFormSchema.safeParse({ accountNumber: '9876543210' });
    expect(result.success).toBe(true);
  });

  it('rejects missing accountNumber field', () => {
    const result = accountFormSchema.safeParse({});
    expect(result.success).toBe(false);
  });

  it('rejects invalid accountNumber in form', () => {
    const result = accountFormSchema.safeParse({ accountNumber: 'abc' });
    expect(result.success).toBe(false);
  });

  it('ignores extra fields', () => {
    const result = accountFormSchema.safeParse({
      accountNumber: '1234567890',
      extra: 'value',
    });
    expect(result.success).toBe(true);
  });
});
