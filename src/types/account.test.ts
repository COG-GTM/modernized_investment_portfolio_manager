import { describe, it, expect } from 'vitest';
import { accountNumberSchema, accountFormSchema } from './account';

describe('accountNumberSchema', () => {
  it('accepts a valid 10-digit number', () => {
    const result = accountNumberSchema.safeParse('1234567890');
    expect(result.success).toBe(true);
  });

  it('rejects a string shorter than 10 digits', () => {
    const result = accountNumberSchema.safeParse('123456789');
    expect(result.success).toBe(false);
  });

  it('rejects a string longer than 10 digits', () => {
    const result = accountNumberSchema.safeParse('12345678901');
    expect(result.success).toBe(false);
  });

  it('rejects non-numeric characters', () => {
    const result = accountNumberSchema.safeParse('12345ABCDE');
    expect(result.success).toBe(false);
  });

  it('rejects an empty string', () => {
    const result = accountNumberSchema.safeParse('');
    expect(result.success).toBe(false);
  });

  it('rejects strings with spaces', () => {
    const result = accountNumberSchema.safeParse('123 456 78');
    expect(result.success).toBe(false);
  });

  it('accepts all zeros (schema only checks format)', () => {
    const result = accountNumberSchema.safeParse('0000000000');
    expect(result.success).toBe(true);
  });
});

describe('accountFormSchema', () => {
  it('validates a complete form with valid account number', () => {
    const result = accountFormSchema.safeParse({ accountNumber: '1234567890' });
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
});
