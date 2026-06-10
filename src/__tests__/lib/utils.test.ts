import { describe, it, expect } from 'vitest';
import { cn } from '../../lib/utils';

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('p-4', 'mt-2')).toBe('p-4 mt-2');
  });

  it('handles conditional classes', () => {
    const result = cn('p-4', false && 'hidden', 'mt-2');
    expect(result).toBe('p-4 mt-2');
  });

  it('handles undefined and null', () => {
    const result = cn('p-4', undefined, null, 'mt-2');
    expect(result).toBe('p-4 mt-2');
  });

  it('merges tailwind conflicts', () => {
    const result = cn('p-4', 'p-8');
    expect(result).toBe('p-8');
  });

  it('handles empty input', () => {
    expect(cn()).toBe('');
  });
});
