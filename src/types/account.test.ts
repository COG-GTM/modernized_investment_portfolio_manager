import { describe, it, expect } from 'vitest';
import { accountNumberSchema, accountFormSchema } from './account';

describe('accountNumberSchema', () => {
  it('accepts a valid 10-digit numeric string', () => {
    const result = accountNumberSchema.safeParse('1234567890');
    expect(result.success).toBe(true);
  });

  it('rejects strings shorter than 10 characters', () => {
    const result = accountNumberSchema.safeParse('123456789');
    expect(result.success).toBe(false);
  });

  it('rejects strings longer than 10 characters', () => {
    const result = accountNumberSchema.safeParse('12345678901');
    expect(result.success).toBe(false);
  });

  it('rejects non-numeric characters', () => {
    const result = accountNumberSchema.safeParse('12345678AB');
    expect(result.success).toBe(false);
  });

  it('rejects empty string', () => {
    const result = accountNumberSchema.safeParse('');
    expect(result.success).toBe(false);
  });

  it('rejects strings with spaces', () => {
    const result = accountNumberSchema.safeParse('123 456 78');
    expect(result.success).toBe(false);
  });

  it('rejects strings with special characters', () => {
    const result = accountNumberSchema.safeParse('123-456-78');
    expect(result.success).toBe(false);
  });

  it('accepts all-zero 10-digit string', () => {
    // The zod schema does not disallow all zeros; it only checks length and digits
    const result = accountNumberSchema.safeParse('0000000000');
    expect(result.success).toBe(true);
  });
});

describe('accountFormSchema', () => {
  it('validates a correct form object', () => {
    const result = accountFormSchema.safeParse({
      accountNumber: '1234567890',
    });
    expect(result.success).toBe(true);
  });

  it('rejects missing accountNumber', () => {
    const result = accountFormSchema.safeParse({});
    expect(result.success).toBe(false);
  });

  it('rejects invalid accountNumber in form', () => {
    const result = accountFormSchema.safeParse({
      accountNumber: 'abc',
    });
    expect(result.success).toBe(false);
  });
});
