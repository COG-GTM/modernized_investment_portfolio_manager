import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react-hooks';
import { useKeyboardNavigation } from './useKeyboardNavigation';

describe('useKeyboardNavigation', () => {
  const onActivate = vi.fn();
  const onNumberKeyActivate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('initializes with selectedIndex of -1', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate })
    );
    expect(result.current.selectedIndex).toBe(-1);
  });

  it('initializes with isKeyboardNavigation as false', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate })
    );
    expect(result.current.isKeyboardNavigation).toBe(false);
  });

  it('returns a containerRef', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate })
    );
    expect(result.current.containerRef).toBeDefined();
  });

  it('moves selection down on ArrowDown', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate })
    );

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }));
    });

    expect(result.current.selectedIndex).toBe(0);
    expect(result.current.isKeyboardNavigation).toBe(true);
  });

  it('moves selection up on ArrowUp with wrapping', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate })
    );

    // Starting at -1, ArrowUp wraps to last item (index 2)
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowUp' }));
    });

    expect(result.current.selectedIndex).toBe(2);
  });

  it('wraps from last to first on ArrowDown', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 2, onActivate })
    );

    // Move to index 0
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }));
    });
    // Move to index 1
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }));
    });
    // Should wrap to index 0
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }));
    });

    expect(result.current.selectedIndex).toBe(0);
  });

  it('calls onActivate on Enter when an item is selected', () => {
    renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate })
    );

    // First select an item
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }));
    });

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
    });

    expect(onActivate).toHaveBeenCalledWith(0);
  });

  it('calls onActivate on Space when an item is selected', () => {
    renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate })
    );

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }));
    });

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: ' ' }));
    });

    expect(onActivate).toHaveBeenCalledWith(0);
  });

  it('does not call onActivate on Enter when no item is selected', () => {
    renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate })
    );

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
    });

    expect(onActivate).not.toHaveBeenCalled();
  });

  it('resets selection on Escape', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate })
    );

    // Select an item
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }));
    });
    expect(result.current.selectedIndex).toBe(0);

    // Press Escape
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
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
      document.dispatchEvent(new KeyboardEvent('keydown', { key: '1' }));
    });

    expect(onNumberKeyActivate).toHaveBeenCalledWith('1');
  });

  it('handles ArrowRight like ArrowDown', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate })
    );

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight' }));
    });

    expect(result.current.selectedIndex).toBe(0);
  });

  it('handles ArrowLeft like ArrowUp', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate })
    );

    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowLeft' }));
    });

    expect(result.current.selectedIndex).toBe(2);
  });

  it('provides a resetSelection function', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate })
    );

    // Select an item first
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown' }));
    });

    act(() => {
      result.current.resetSelection();
    });

    expect(result.current.selectedIndex).toBe(-1);
  });

  it('provides an announceToScreenReader function', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate })
    );

    expect(typeof result.current.announceToScreenReader).toBe('function');
  });

  it('clamps selection without wrap', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({
        itemCount: 2,
        onActivate,
        focusOptions: { wrap: false, skipDisabled: false, announceChanges: false },
      })
    );

    // Try to go up from -1 without wrapping
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowUp' }));
    });

    // Should clamp to 0
    expect(result.current.selectedIndex).toBe(0);
  });
});
