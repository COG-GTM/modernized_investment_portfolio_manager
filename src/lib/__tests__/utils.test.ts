import { describe, it, expect } from 'vitest';
import { cn } from '../utils';

describe('cn', () => {
  it('handles a single class string', () => {
    expect(cn('px-2')).toBe('px-2');
  });

  it('merges multiple class strings', () => {
    expect(cn('px-2', 'py-4')).toBe('px-2 py-4');
  });

  it('handles conditional classes with clsx', () => {
    expect(cn('base', false && 'hidden', 'visible')).toBe('base visible');
    expect(cn('base', true && 'active')).toBe('base active');
  });

  it('resolves Tailwind merge conflicts', () => {
    expect(cn('px-2', 'px-4')).toBe('px-4');
    expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500');
    expect(cn('mt-2 p-4', 'mt-4')).toBe('p-4 mt-4');
  });
});
