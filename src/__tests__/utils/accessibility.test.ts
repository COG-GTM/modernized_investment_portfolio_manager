import { describe, it, expect, vi, beforeEach } from 'vitest';
import { focusElement, trapFocus, generateAriaLabel } from '../../utils/accessibility';

describe('focusElement', () => {
  it('focuses and scrolls element', () => {
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

  it('does nothing for null', () => {
    expect(() => focusElement(null)).not.toThrow();
  });

  it('passes focus options', () => {
    const el = document.createElement('button');
    el.focus = vi.fn();
    el.scrollIntoView = vi.fn();
    focusElement(el, { preventScroll: true });
    expect(el.focus).toHaveBeenCalledWith({ preventScroll: true });
  });
});

describe('trapFocus', () => {
  it('returns cleanup function', () => {
    const container = document.createElement('div');
    const btn1 = document.createElement('button');
    const btn2 = document.createElement('button');
    container.appendChild(btn1);
    container.appendChild(btn2);
    document.body.appendChild(container);

    const cleanup = trapFocus(container);
    expect(typeof cleanup).toBe('function');
    cleanup();
    document.body.removeChild(container);
  });

  it('focuses first element', () => {
    const container = document.createElement('div');
    const btn = document.createElement('button');
    btn.focus = vi.fn();
    container.appendChild(btn);
    document.body.appendChild(container);

    trapFocus(container);
    expect(btn.focus).toHaveBeenCalled();
    document.body.removeChild(container);
  });

  it('traps Tab forward from last to first', () => {
    const container = document.createElement('div');
    const btn1 = document.createElement('button');
    const btn2 = document.createElement('button');
    btn1.focus = vi.fn();
    btn2.focus = vi.fn();
    container.appendChild(btn1);
    container.appendChild(btn2);
    document.body.appendChild(container);

    trapFocus(container);
    // Simulate focus on last element
    Object.defineProperty(document, 'activeElement', { value: btn2, configurable: true });
    const event = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true });
    Object.defineProperty(event, 'preventDefault', { value: vi.fn() });
    container.dispatchEvent(event);
    expect(btn1.focus).toHaveBeenCalled();
    document.body.removeChild(container);
  });

  it('traps Shift+Tab backward from first to last', () => {
    const container = document.createElement('div');
    const btn1 = document.createElement('button');
    const btn2 = document.createElement('button');
    btn1.focus = vi.fn();
    btn2.focus = vi.fn();
    container.appendChild(btn1);
    container.appendChild(btn2);
    document.body.appendChild(container);

    trapFocus(container);
    // Simulate focus on first element
    Object.defineProperty(document, 'activeElement', { value: btn1, configurable: true });
    const event = new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true });
    Object.defineProperty(event, 'preventDefault', { value: vi.fn() });
    container.dispatchEvent(event);
    expect(btn2.focus).toHaveBeenCalled();
    document.body.removeChild(container);
  });

  it('ignores non-Tab keys', () => {
    const container = document.createElement('div');
    const btn1 = document.createElement('button');
    container.appendChild(btn1);
    document.body.appendChild(container);

    trapFocus(container);
    const event = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true });
    container.dispatchEvent(event);
    document.body.removeChild(container);
  });
});

describe('generateAriaLabel', () => {
  it('returns label only', () => {
    expect(generateAriaLabel('Submit')).toBe('Submit');
  });

  it('includes shortcut', () => {
    expect(generateAriaLabel('Submit', 'Enter')).toBe('Submit - Press Enter');
  });

  it('includes description', () => {
    expect(generateAriaLabel('Submit', undefined, 'Save form')).toBe('Submit - Save form');
  });

  it('includes both shortcut and description', () => {
    expect(generateAriaLabel('Submit', 'Enter', 'Save form')).toBe('Submit - Press Enter - Save form');
  });
});
