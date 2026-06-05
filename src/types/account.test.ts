import { describe, it, expect } from 'vitest';
import { accountNumberSchema, accountFormSchema } from './account';

describe('accountNumberSchema', () => {
  it('accepts valid 10-digit number', () => {
    expect(accountNumberSchema.parse('1234567890')).toBe('1234567890');
  });

  it('rejects short string', () => {
    expect(() => accountNumberSchema.parse('123456789')).toThrow();
  });

  it('rejects long string', () => {
    expect(() => accountNumberSchema.parse('12345678901')).toThrow();
  });

  it('rejects non-numeric', () => {
    expect(() => accountNumberSchema.parse('123456789a')).toThrow();
  });

  it('rejects empty string', () => {
    expect(() => accountNumberSchema.parse('')).toThrow();
  });

  it('accepts all zeros', () => {
    expect(accountNumberSchema.parse('0000000000')).toBe('0000000000');
  });
});

describe('accountFormSchema', () => {
  it('accepts valid form data', () => {
    const result = accountFormSchema.parse({ accountNumber: '1234567890' });
    expect(result.accountNumber).toBe('1234567890');
  });

  it('rejects missing accountNumber', () => {
    expect(() => accountFormSchema.parse({})).toThrow();
  });

  it('rejects invalid accountNumber', () => {
    expect(() => accountFormSchema.parse({ accountNumber: 'abc' })).toThrow();
  });
});
