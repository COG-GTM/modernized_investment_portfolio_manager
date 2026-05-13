import { describe, it, expect, vi } from 'vitest';
import { focusElement, generateAriaLabel } from '../accessibility';

describe('focusElement', () => {
  it('does not throw when called with null', () => {
    expect(() => focusElement(null)).not.toThrow();
  });

  it('calls focus and scrollIntoView on a valid element', () => {
    const element = document.createElement('button');
    element.focus = vi.fn();
    element.scrollIntoView = vi.fn();

    focusElement(element);

    expect(element.focus).toHaveBeenCalled();
    expect(element.scrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'nearest',
      inline: 'nearest',
    });
  });
});

describe('generateAriaLabel', () => {
  it('returns label only when no extras provided', () => {
    expect(generateAriaLabel('Save')).toBe('Save');
  });

  it('includes shortcut when provided', () => {
    expect(generateAriaLabel('Save', 'Ctrl+S')).toBe('Save - Press Ctrl+S');
  });

  it('includes description when provided', () => {
    expect(generateAriaLabel('Save', undefined, 'Saves the current document')).toBe(
      'Save - Saves the current document'
    );
  });

  it('includes both shortcut and description', () => {
    expect(generateAriaLabel('Save', 'Ctrl+S', 'Saves the current document')).toBe(
      'Save - Press Ctrl+S - Saves the current document'
    );
  });
});
