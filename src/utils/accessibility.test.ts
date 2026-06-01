import { describe, it, expect, vi, beforeEach } from 'vitest';
import { focusElement, trapFocus, generateAriaLabel } from './accessibility';

describe('focusElement', () => {
  it('focuses the given element', () => {
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

  it('passes focus options to focus()', () => {
    const element = document.createElement('button');
    element.focus = vi.fn();
    element.scrollIntoView = vi.fn();

    focusElement(element, { preventScroll: true });

    expect(element.focus).toHaveBeenCalledWith({ preventScroll: true });
  });

  it('does nothing when element is null', () => {
    // Should not throw
    focusElement(null);
  });
});

describe('trapFocus', () => {
  let container: HTMLDivElement;
  let firstButton: HTMLButtonElement;
  let lastButton: HTMLButtonElement;

  beforeEach(() => {
    container = document.createElement('div');
    firstButton = document.createElement('button');
    firstButton.textContent = 'First';
    lastButton = document.createElement('button');
    lastButton.textContent = 'Last';
    container.appendChild(firstButton);
    container.appendChild(lastButton);
    document.body.appendChild(container);
  });

  it('focuses the first focusable element', () => {
    firstButton.focus = vi.fn();
    trapFocus(container);
    expect(firstButton.focus).toHaveBeenCalled();
  });

  it('returns a cleanup function', () => {
    const cleanup = trapFocus(container);
    expect(typeof cleanup).toBe('function');
  });

  it('cleanup removes the event listener', () => {
    const removeEventListenerSpy = vi.spyOn(container, 'removeEventListener');
    const cleanup = trapFocus(container);
    cleanup();
    expect(removeEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function));
  });

  it('wraps focus from last to first on Tab', () => {
    trapFocus(container);

    // Simulate last element being focused
    lastButton.focus();
    Object.defineProperty(document, 'activeElement', {
      value: lastButton,
      writable: true,
      configurable: true,
    });

    const tabEvent = new KeyboardEvent('keydown', {
      key: 'Tab',
      bubbles: true,
    });
    const preventDefaultSpy = vi.spyOn(tabEvent, 'preventDefault');
    firstButton.focus = vi.fn();
    container.dispatchEvent(tabEvent);

    expect(preventDefaultSpy).toHaveBeenCalled();
    expect(firstButton.focus).toHaveBeenCalled();
  });

  it('wraps focus from first to last on Shift+Tab', () => {
    trapFocus(container);

    // Simulate first element being focused
    firstButton.focus();
    Object.defineProperty(document, 'activeElement', {
      value: firstButton,
      writable: true,
      configurable: true,
    });

    const tabEvent = new KeyboardEvent('keydown', {
      key: 'Tab',
      shiftKey: true,
      bubbles: true,
    });
    const preventDefaultSpy = vi.spyOn(tabEvent, 'preventDefault');
    lastButton.focus = vi.fn();
    container.dispatchEvent(tabEvent);

    expect(preventDefaultSpy).toHaveBeenCalled();
    expect(lastButton.focus).toHaveBeenCalled();
  });

  it('does not trap on non-Tab keys', () => {
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
    expect(generateAriaLabel('Save', undefined, 'Save your work')).toBe('Save - Save your work');
  });

  it('includes both shortcut and description', () => {
    expect(generateAriaLabel('Save', 'Ctrl+S', 'Save your work')).toBe(
      'Save - Press Ctrl+S - Save your work'
    );
  });

  it('handles empty strings', () => {
    expect(generateAriaLabel('')).toBe('');
  });
});
