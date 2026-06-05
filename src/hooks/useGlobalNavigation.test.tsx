import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react-hooks';
import { MemoryRouter } from 'react-router-dom';
import { useGlobalNavigation } from './useGlobalNavigation';
import type { ReactNode } from 'react';

function wrapper({ children }: { children: ReactNode }) {
  return <MemoryRouter initialEntries={['/portfolio-inquiry']}>{children}</MemoryRouter>;
}

function homeWrapper({ children }: { children: ReactNode }) {
  return <MemoryRouter initialEntries={['/']}>{children}</MemoryRouter>;
}

describe('useGlobalNavigation', () => {
  it('renders without error', () => {
    const { result } = renderHook(() => useGlobalNavigation(), {
      wrapper,
    });
    expect(result).toBeTruthy();
  });

  it('does not navigate on Escape when on main menu', () => {
    renderHook(() => useGlobalNavigation(), { wrapper: homeWrapper });

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })
      );
    });
  });

  it('does not navigate when input is focused', () => {
    renderHook(() => useGlobalNavigation(), { wrapper });

    const input = document.createElement('input');
    document.body.appendChild(input);
    input.focus();

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })
      );
    });

    document.body.removeChild(input);
  });

  it('does not navigate when modal is open', () => {
    renderHook(() => useGlobalNavigation(), { wrapper });

    const modal = document.createElement('div');
    modal.setAttribute('aria-modal', 'true');
    document.body.appendChild(modal);

    act(() => {
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })
      );
    });

    document.body.removeChild(modal);
  });

  it('cleans up event listener on unmount', () => {
    const removeEventSpy = vi.spyOn(document, 'removeEventListener');
    const { unmount } = renderHook(() => useGlobalNavigation(), {
      wrapper,
    });
    unmount();
    expect(removeEventSpy).toHaveBeenCalledWith('keydown', expect.any(Function));
    removeEventSpy.mockRestore();
  });
});
