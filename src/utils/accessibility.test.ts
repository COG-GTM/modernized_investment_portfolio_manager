import { describe, it, expect, vi, beforeEach } from 'vitest';
import { focusElement, trapFocus, generateAriaLabel } from './accessibility';

describe('focusElement', () => {
  it('calls focus on element', () => {
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

  it('handles null element', () => {
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
  let container: HTMLDivElement;

  beforeEach(() => {
    container = document.createElement('div');
    const btn1 = document.createElement('button');
    btn1.textContent = 'First';
    const btn2 = document.createElement('button');
    btn2.textContent = 'Last';
    container.appendChild(btn1);
    container.appendChild(btn2);
    document.body.appendChild(container);
  });

  it('returns cleanup function', () => {
    const cleanup = trapFocus(container);
    expect(typeof cleanup).toBe('function');
    cleanup();
  });

  it('focuses first element', () => {
    const firstBtn = container.querySelector('button')!;
    firstBtn.focus = vi.fn();
    trapFocus(container);
    expect(firstBtn.focus).toHaveBeenCalled();
  });

  it('traps focus on Tab from last element', () => {
    const buttons = container.querySelectorAll('button');
    const firstBtn = buttons[0] as HTMLElement;
    const lastBtn = buttons[1] as HTMLElement;
    firstBtn.focus = vi.fn();
    trapFocus(container);

    Object.defineProperty(document, 'activeElement', {
      value: lastBtn,
      writable: true,
      configurable: true,
    });

    const event = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true });
    const spy = vi.spyOn(event, 'preventDefault');
    container.dispatchEvent(event);
    expect(spy).toHaveBeenCalled();
  });

  it('traps focus on Shift+Tab from first element', () => {
    const buttons = container.querySelectorAll('button');
    const firstBtn = buttons[0] as HTMLElement;
    firstBtn.focus = vi.fn();
    trapFocus(container);

    Object.defineProperty(document, 'activeElement', {
      value: firstBtn,
      writable: true,
      configurable: true,
    });

    const event = new KeyboardEvent('keydown', {
      key: 'Tab',
      shiftKey: true,
      bubbles: true,
    });
    const spy = vi.spyOn(event, 'preventDefault');
    container.dispatchEvent(event);
    expect(spy).toHaveBeenCalled();
  });

  it('ignores non-Tab keys', () => {
    trapFocus(container);
    const event = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true });
    const spy = vi.spyOn(event, 'preventDefault');
    container.dispatchEvent(event);
    expect(spy).not.toHaveBeenCalled();
  });
});

describe('generateAriaLabel', () => {
  it('generates label with just label', () => {
    expect(generateAriaLabel('Portfolio')).toBe('Portfolio');
  });

  it('generates label with shortcut', () => {
    expect(generateAriaLabel('Portfolio', '1')).toBe('Portfolio - Press 1');
  });

  it('generates label with description', () => {
    expect(generateAriaLabel('Portfolio', undefined, 'View portfolio')).toBe(
      'Portfolio - View portfolio'
    );
  });

  it('generates label with all parts', () => {
    expect(generateAriaLabel('Portfolio', '1', 'View portfolio')).toBe(
      'Portfolio - Press 1 - View portfolio'
    );
  });
});
