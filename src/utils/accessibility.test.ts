import { describe, it, expect, vi, beforeEach } from 'vitest';
import { focusElement, trapFocus, generateAriaLabel } from './accessibility';

describe('focusElement', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('calls focus and scrollIntoView on the element', () => {
    const el = document.createElement('button');
    el.focus = vi.fn();
    el.scrollIntoView = vi.fn();

    focusElement(el);

    expect(el.focus).toHaveBeenCalled();
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
    expect(() => focusElement(null)).not.toThrow();
  });
});

describe('trapFocus', () => {
  it('returns a cleanup function', () => {
    const container = document.createElement('div');
    const btn1 = document.createElement('button');
    const btn2 = document.createElement('button');
    container.appendChild(btn1);
    container.appendChild(btn2);
    document.body.appendChild(container);

    const cleanup = trapFocus(container);
    expect(typeof cleanup).toBe('function');

    cleanup();
  });

  it('focuses the first focusable element', () => {
    const container = document.createElement('div');
    const input = document.createElement('input');
    const btn = document.createElement('button');
    container.appendChild(input);
    container.appendChild(btn);
    document.body.appendChild(container);

    input.focus = vi.fn();
    trapFocus(container);

    expect(input.focus).toHaveBeenCalled();
  });
});

describe('generateAriaLabel', () => {
  it('returns just the label when no extras', () => {
    expect(generateAriaLabel('Save')).toBe('Save');
  });

  it('appends shortcut info', () => {
    expect(generateAriaLabel('Save', 'Ctrl+S')).toBe('Save - Press Ctrl+S');
  });

  it('appends description', () => {
    expect(generateAriaLabel('Save', undefined, 'Save the document')).toBe(
      'Save - Save the document'
    );
  });

  it('appends both shortcut and description', () => {
    expect(generateAriaLabel('Save', 'Ctrl+S', 'Save the document')).toBe(
      'Save - Press Ctrl+S - Save the document'
    );
  });
});
