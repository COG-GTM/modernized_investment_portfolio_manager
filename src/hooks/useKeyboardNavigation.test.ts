import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react-hooks';
import { useKeyboardNavigation } from './useKeyboardNavigation';

describe('useKeyboardNavigation', () => {
  const onActivate = vi.fn();
  const onNumberKeyActivate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with selectedIndex -1', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({
        itemCount: 3,
        onActivate,
      })
    );
    expect(result.current.selectedIndex).toBe(-1);
    expect(result.current.isKeyboardNavigation).toBe(false);
  });

  it('moves selection down on ArrowDown', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({
        itemCount: 3,
        onActivate,
      })
    );

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true })
      );
    });

    expect(result.current.selectedIndex).toBe(0);
    expect(result.current.isKeyboardNavigation).toBe(true);
  });

  it('moves selection up on ArrowUp', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({
        itemCount: 3,
        onActivate,
      })
    );

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true })
      );
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true })
      );
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'ArrowUp', bubbles: true })
      );
    });

    expect(result.current.selectedIndex).toBe(0);
  });

  it('wraps around from last to first', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({
        itemCount: 2,
        onActivate,
      })
    );

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true })
      );
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true })
      );
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true })
      );
    });

    expect(result.current.selectedIndex).toBe(0);
  });

  it('wraps around from first to last on ArrowUp', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({
        itemCount: 3,
        onActivate,
      })
    );

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'ArrowUp', bubbles: true })
      );
    });

    expect(result.current.selectedIndex).toBe(2);
  });

  it('activates on Enter when item selected', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({
        itemCount: 3,
        onActivate,
      })
    );

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true })
      );
    });

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'Enter', bubbles: true })
      );
    });

    expect(onActivate).toHaveBeenCalledWith(0);
  });

  it('activates on Space', () => {
    renderHook(() =>
      useKeyboardNavigation({
        itemCount: 3,
        onActivate,
      })
    );

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true })
      );
    });

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: ' ', bubbles: true })
      );
    });

    expect(onActivate).toHaveBeenCalledWith(0);
  });

  it('resets on Escape', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({
        itemCount: 3,
        onActivate,
      })
    );

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true })
      );
    });

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })
      );
    });

    expect(result.current.selectedIndex).toBe(-1);
    expect(result.current.isKeyboardNavigation).toBe(false);
  });

  it('calls onNumberKeyActivate for number keys', () => {
    renderHook(() =>
      useKeyboardNavigation({
        itemCount: 3,
        onActivate,
        onNumberKeyActivate,
      })
    );

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: '1', bubbles: true })
      );
    });

    expect(onNumberKeyActivate).toHaveBeenCalledWith('1');
  });

  it('handles ArrowRight like ArrowDown', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({
        itemCount: 3,
        onActivate,
      })
    );

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true })
      );
    });

    expect(result.current.selectedIndex).toBe(0);
  });

  it('handles ArrowLeft like ArrowUp', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({
        itemCount: 3,
        onActivate,
      })
    );

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'ArrowLeft', bubbles: true })
      );
    });

    expect(result.current.selectedIndex).toBe(2);
  });

  it('provides resetSelection function', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({
        itemCount: 3,
        onActivate,
      })
    );

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true })
      );
    });

    act(() => {
      result.current.resetSelection();
    });

    expect(result.current.selectedIndex).toBe(-1);
  });

  it('provides announceToScreenReader function', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({
        itemCount: 3,
        onActivate,
      })
    );

    expect(typeof result.current.announceToScreenReader).toBe('function');
  });

  it('provides containerRef', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({
        itemCount: 3,
        onActivate,
      })
    );

    expect(result.current.containerRef).toBeDefined();
  });
});
