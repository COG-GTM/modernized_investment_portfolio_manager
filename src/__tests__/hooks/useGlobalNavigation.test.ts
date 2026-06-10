import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react-hooks';
import { createElement } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { useGlobalNavigation } from '../../hooks/useGlobalNavigation';

function fireEscape() {
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
}

function renderGlobalNav(initialPath: string) {
  return renderHook(() => useGlobalNavigation(), {
    wrapper: ({ children }: { children?: React.ReactNode }) =>
      createElement(MemoryRouter, { initialEntries: [initialPath] }, children),
  });
}

describe('useGlobalNavigation', () => {
  it('does nothing on Escape when on main menu', () => {
    renderGlobalNav('/');
    act(() => { fireEscape(); });
  });

  it('does not navigate when active element is input', () => {
    renderGlobalNav('/portfolio-inquiry');
    const input = document.createElement('input');
    document.body.appendChild(input);
    input.focus();
    act(() => { fireEscape(); });
    document.body.removeChild(input);
  });

  it('does not navigate when active element is textarea', () => {
    renderGlobalNav('/portfolio-inquiry');
    const textarea = document.createElement('textarea');
    document.body.appendChild(textarea);
    textarea.focus();
    act(() => { fireEscape(); });
    document.body.removeChild(textarea);
  });

  it('does not navigate when modal is open', () => {
    renderGlobalNav('/portfolio-inquiry');
    const modal = document.createElement('div');
    modal.setAttribute('aria-modal', 'true');
    document.body.appendChild(modal);
    act(() => { fireEscape(); });
    document.body.removeChild(modal);
  });

  it('cleans up event listener on unmount', () => {
    const removeListenerSpy = vi.spyOn(document, 'removeEventListener');
    const { unmount } = renderGlobalNav('/portfolio-inquiry');
    unmount();
    expect(removeListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function));
    removeListenerSpy.mockRestore();
  });
});
