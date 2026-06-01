import { describe, it, expect, vi, beforeEach } from 'vitest';
import { focusElement, generateAriaLabel } from './accessibility';

describe('focusElement', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('calls focus and scrollIntoView on the element', () => {
    const el = document.createElement('button');
    el.focus = vi.fn();
    el.scrollIntoView = vi.fn();

    focusElement(el);

    expect(el.focus).toHaveBeenCalledWith(undefined);
    expect(el.scrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'nearest',
      inline: 'nearest',
    });
  });

  it('passes focus options through', () => {
    const el = document.createElement('input');
    el.focus = vi.fn();
    el.scrollIntoView = vi.fn();

    focusElement(el, { preventScroll: true });

    expect(el.focus).toHaveBeenCalledWith({ preventScroll: true });
  });

  it('does nothing when element is null', () => {
    // Should not throw
    focusElement(null);
  });
});

describe('generateAriaLabel', () => {
  it('returns just the label when no shortcut or description', () => {
    expect(generateAriaLabel('Submit')).toBe('Submit');
  });

  it('includes shortcut', () => {
    expect(generateAriaLabel('Save', 'Ctrl+S')).toBe('Save - Press Ctrl+S');
  });

  it('includes description', () => {
    expect(generateAriaLabel('Open', undefined, 'Opens the dialog')).toBe(
      'Open - Opens the dialog'
    );
  });

  it('includes both shortcut and description', () => {
    expect(generateAriaLabel('Save', 'Ctrl+S', 'Saves your work')).toBe(
      'Save - Press Ctrl+S - Saves your work'
    );
  });

  it('handles empty string label', () => {
    expect(generateAriaLabel('')).toBe('');
  });
});
