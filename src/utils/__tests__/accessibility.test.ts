import { describe, it, expect, vi, beforeEach } from 'vitest';
import { focusElement, trapFocus, generateAriaLabel } from '../accessibility';

describe('focusElement', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('focuses the given element', () => {
    const el = document.createElement('button');
    document.body.appendChild(el);
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

  it('does nothing when element is null', () => {
    // Should not throw
    focusElement(null);
  });

  it('passes focus options through', () => {
    const el = document.createElement('input');
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

  it('focuses the first focusable element on setup', () => {
    const container = document.createElement('div');
    const btn1 = document.createElement('button');
    btn1.textContent = 'First';
    const btn2 = document.createElement('button');
    btn2.textContent = 'Second';
    container.appendChild(btn1);
    container.appendChild(btn2);
    document.body.appendChild(container);

    btn1.focus = vi.fn();

    trapFocus(container);

    expect(btn1.focus).toHaveBeenCalled();
  });

  it('returns a cleanup function', () => {
    const container = document.createElement('div');
    const btn = document.createElement('button');
    container.appendChild(btn);
    document.body.appendChild(container);

    const removeEventListenerSpy = vi.spyOn(container, 'removeEventListener');
    const cleanup = trapFocus(container);

    expect(typeof cleanup).toBe('function');
    cleanup();
    expect(removeEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function));
  });

  it('wraps focus from last to first on Tab', () => {
    const container = document.createElement('div');
    const btn1 = document.createElement('button');
    btn1.textContent = 'First';
    const btn2 = document.createElement('button');
    btn2.textContent = 'Last';
    container.appendChild(btn1);
    container.appendChild(btn2);
    document.body.appendChild(container);

    btn1.focus = vi.fn();
    btn2.focus = vi.fn();

    trapFocus(container);

    // Simulate being on the last element and pressing Tab
    Object.defineProperty(document, 'activeElement', {
      value: btn2,
      writable: true,
      configurable: true,
    });

    const tabEvent = new KeyboardEvent('keydown', {
      key: 'Tab',
      bubbles: true,
    });
    const preventDefaultSpy = vi.spyOn(tabEvent, 'preventDefault');
    container.dispatchEvent(tabEvent);

    expect(preventDefaultSpy).toHaveBeenCalled();
    expect(btn1.focus).toHaveBeenCalled();
  });

  it('wraps focus from first to last on Shift+Tab', () => {
    const container = document.createElement('div');
    const btn1 = document.createElement('button');
    btn1.textContent = 'First';
    const btn2 = document.createElement('button');
    btn2.textContent = 'Last';
    container.appendChild(btn1);
    container.appendChild(btn2);
    document.body.appendChild(container);

    btn1.focus = vi.fn();
    btn2.focus = vi.fn();

    trapFocus(container);

    // Simulate being on the first element and pressing Shift+Tab
    Object.defineProperty(document, 'activeElement', {
      value: btn1,
      writable: true,
      configurable: true,
    });

    const shiftTabEvent = new KeyboardEvent('keydown', {
      key: 'Tab',
      shiftKey: true,
      bubbles: true,
    });
    const preventDefaultSpy = vi.spyOn(shiftTabEvent, 'preventDefault');
    container.dispatchEvent(shiftTabEvent);

    expect(preventDefaultSpy).toHaveBeenCalled();
    expect(btn2.focus).toHaveBeenCalled();
  });

  it('ignores non-Tab keys', () => {
    const container = document.createElement('div');
    const btn = document.createElement('button');
    container.appendChild(btn);
    document.body.appendChild(container);

    trapFocus(container);

    const enterEvent = new KeyboardEvent('keydown', {
      key: 'Enter',
      bubbles: true,
    });
    const preventDefaultSpy = vi.spyOn(enterEvent, 'preventDefault');
    container.dispatchEvent(enterEvent);

    expect(preventDefaultSpy).not.toHaveBeenCalled();
  });
});

describe('generateAriaLabel', () => {
  it('returns just the label when no shortcut or description', () => {
    expect(generateAriaLabel('Save')).toBe('Save');
  });

  it('includes shortcut when provided', () => {
    expect(generateAriaLabel('Save', 'Ctrl+S')).toBe('Save - Press Ctrl+S');
  });

  it('includes description when provided', () => {
    expect(generateAriaLabel('Save', undefined, 'Saves the document')).toBe(
      'Save - Saves the document'
    );
  });

  it('includes both shortcut and description', () => {
    expect(generateAriaLabel('Save', 'Ctrl+S', 'Saves the document')).toBe(
      'Save - Press Ctrl+S - Saves the document'
    );
  });

  it('handles empty string label', () => {
    expect(generateAriaLabel('')).toBe('');
  });
});
