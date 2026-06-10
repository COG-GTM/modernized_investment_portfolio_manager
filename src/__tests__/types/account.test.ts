import { describe, it, expect } from 'vitest';
import { accountNumberSchema, accountFormSchema } from '../../types/account';

describe('accountNumberSchema', () => {
  it('accepts valid 10-digit number', () => {
    expect(() => accountNumberSchema.parse('1234567890')).not.toThrow();
  });

  it('rejects short numbers', () => {
    expect(() => accountNumberSchema.parse('12345')).toThrow();
  });

  it('rejects long numbers', () => {
    expect(() => accountNumberSchema.parse('12345678901')).toThrow();
  });

  it('rejects non-numeric characters', () => {
    expect(() => accountNumberSchema.parse('123456789A')).toThrow();
  });

  it('rejects empty string', () => {
    expect(() => accountNumberSchema.parse('')).toThrow();
  });
});

describe('accountFormSchema', () => {
  it('validates valid form data', () => {
    const result = accountFormSchema.safeParse({ accountNumber: '1234567890' });
    expect(result.success).toBe(true);
  });

  it('rejects invalid account number', () => {
    const result = accountFormSchema.safeParse({ accountNumber: 'bad' });
    expect(result.success).toBe(false);
  });

  it('rejects missing account number', () => {
    const result = accountFormSchema.safeParse({});
    expect(result.success).toBe(false);
  });
});
