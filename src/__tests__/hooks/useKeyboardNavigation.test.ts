import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react-hooks';
import { useKeyboardNavigation } from '../../hooks/useKeyboardNavigation';

function fireKey(key: string) {
  document.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true }));
}

describe('useKeyboardNavigation', () => {
  it('returns initial state', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate: vi.fn() })
    );
    expect(result.current.selectedIndex).toBe(-1);
    expect(result.current.isKeyboardNavigation).toBe(false);
    expect(result.current.containerRef).toBeDefined();
  });

  it('moves down on ArrowDown', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate: vi.fn() })
    );
    act(() => { fireKey('ArrowDown'); });
    expect(result.current.selectedIndex).toBe(0);
    expect(result.current.isKeyboardNavigation).toBe(true);
  });

  it('moves up on ArrowUp (wraps)', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate: vi.fn() })
    );
    act(() => { fireKey('ArrowUp'); });
    expect(result.current.selectedIndex).toBe(2);
  });

  it('wraps from last to first on ArrowDown', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 2, onActivate: vi.fn() })
    );
    act(() => { fireKey('ArrowDown'); });
    act(() => { fireKey('ArrowDown'); });
    act(() => { fireKey('ArrowDown'); });
    expect(result.current.selectedIndex).toBe(0);
  });

  it('moves right on ArrowRight', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate: vi.fn() })
    );
    act(() => { fireKey('ArrowRight'); });
    expect(result.current.selectedIndex).toBe(0);
  });

  it('moves left on ArrowLeft', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate: vi.fn() })
    );
    act(() => { fireKey('ArrowLeft'); });
    expect(result.current.selectedIndex).toBe(2);
  });

  it('activates on Enter', () => {
    const onActivate = vi.fn();
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate })
    );
    act(() => { fireKey('ArrowDown'); });
    act(() => { fireKey('Enter'); });
    expect(onActivate).toHaveBeenCalledWith(0);
  });

  it('activates on Space', () => {
    const onActivate = vi.fn();
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate })
    );
    act(() => { fireKey('ArrowDown'); });
    act(() => { fireKey(' '); });
    expect(onActivate).toHaveBeenCalledWith(0);
  });

  it('does not activate on Enter when no selection', () => {
    const onActivate = vi.fn();
    renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate })
    );
    act(() => { fireKey('Enter'); });
    expect(onActivate).not.toHaveBeenCalled();
  });

  it('resets on Escape', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate: vi.fn() })
    );
    act(() => { fireKey('ArrowDown'); });
    expect(result.current.selectedIndex).toBe(0);
    act(() => { fireKey('Escape'); });
    expect(result.current.selectedIndex).toBe(-1);
    expect(result.current.isKeyboardNavigation).toBe(false);
  });

  it('calls onNumberKeyActivate for number keys', () => {
    const onNumberKeyActivate = vi.fn();
    renderHook(() =>
      useKeyboardNavigation({
        itemCount: 3,
        onActivate: vi.fn(),
        onNumberKeyActivate,
      })
    );
    act(() => { fireKey('1'); });
    expect(onNumberKeyActivate).toHaveBeenCalledWith('1');
    act(() => { fireKey('2'); });
    expect(onNumberKeyActivate).toHaveBeenCalledWith('2');
    act(() => { fireKey('3'); });
    expect(onNumberKeyActivate).toHaveBeenCalledWith('3');
  });

  it('resetSelection resets state', () => {
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate: vi.fn() })
    );
    act(() => { fireKey('ArrowDown'); });
    act(() => { result.current.resetSelection(); });
    expect(result.current.selectedIndex).toBe(-1);
  });

  it('announceToScreenReader appends and removes element', () => {
    vi.useFakeTimers();
    const { result } = renderHook(() =>
      useKeyboardNavigation({ itemCount: 3, onActivate: vi.fn() })
    );
    act(() => { result.current.announceToScreenReader('test message'); });
    const liveRegion = document.querySelector('[aria-live="polite"]');
    expect(liveRegion).not.toBeNull();
    expect(liveRegion?.textContent).toBe('test message');
    act(() => { vi.advanceTimersByTime(1100); });
    expect(document.querySelector('[aria-live="polite"]')).toBeNull();
    vi.useRealTimers();
  });
});
