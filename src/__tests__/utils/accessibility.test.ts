import { describe, it, expect, vi, beforeEach } from 'vitest';
import { focusElement, trapFocus, generateAriaLabel } from '../../utils/accessibility';

describe('focusElement', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('does nothing when element is null', () => {
    expect(() => focusElement(null)).not.toThrow();
  });

  it('calls focus on the element', () => {
    const el = document.createElement('button');
    document.body.appendChild(el);
    el.focus = vi.fn();
    el.scrollIntoView = vi.fn();

    focusElement(el);

    expect(el.focus).toHaveBeenCalled();
  });

  it('calls scrollIntoView with smooth behavior', () => {
    const el = document.createElement('button');
    document.body.appendChild(el);
    el.focus = vi.fn();
    el.scrollIntoView = vi.fn();

    focusElement(el);

    expect(el.scrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'nearest',
      inline: 'nearest',
    });
  });

  it('passes focus options through', () => {
    const el = document.createElement('button');
    document.body.appendChild(el);
    el.focus = vi.fn();
    el.scrollIntoView = vi.fn();

    focusElement(el, { preventScroll: true });

    expect(el.focus).toHaveBeenCalledWith({ preventScroll: true });
  });
});

describe('trapFocus', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('focuses the first focusable element', () => {
    const container = document.createElement('div');
    const btn1 = document.createElement('button');
    btn1.textContent = 'First';
    const btn2 = document.createElement('button');
    btn2.textContent = 'Second';
    container.appendChild(btn1);
    container.appendChild(btn2);
    document.body.appendChild(container);

    trapFocus(container);

    expect(document.activeElement).toBe(btn1);
  });

  it('returns a cleanup function', () => {
    const container = document.createElement('div');
    const btn = document.createElement('button');
    container.appendChild(btn);
    document.body.appendChild(container);

    const cleanup = trapFocus(container);

    expect(typeof cleanup).toBe('function');
  });

  it('cleanup removes the event listener', () => {
    const container = document.createElement('div');
    const btn = document.createElement('button');
    container.appendChild(btn);
    document.body.appendChild(container);

    const spy = vi.spyOn(container, 'removeEventListener');
    const cleanup = trapFocus(container);
    cleanup();

    expect(spy).toHaveBeenCalledWith('keydown', expect.any(Function));
  });
});

describe('generateAriaLabel', () => {
  it('returns just the label when no shortcut or description', () => {
    expect(generateAriaLabel('Click me')).toBe('Click me');
  });

  it('includes shortcut when provided', () => {
    expect(generateAriaLabel('Save', 'Ctrl+S')).toBe('Save - Press Ctrl+S');
  });

  it('includes description when provided', () => {
    expect(generateAriaLabel('Save', undefined, 'Save the document')).toBe(
      'Save - Save the document'
    );
  });

  it('includes both shortcut and description', () => {
    expect(generateAriaLabel('Save', 'Ctrl+S', 'Save the document')).toBe(
      'Save - Press Ctrl+S - Save the document'
    );
  });

  it('handles empty strings', () => {
    expect(generateAriaLabel('')).toBe('');
  });
});
