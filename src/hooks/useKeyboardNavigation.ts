import { useState, useEffect, useCallback, useRef } from 'react';
import { KeyboardNavigationState, NavigationDirection, FocusManagementOptions } from '../types/navigation';

interface UseKeyboardNavigationProps {
  itemCount: number;
  onActivate: (index: number) => void;
  onNumberKeyActivate?: (key: string) => void;
  focusOptions?: FocusManagementOptions;
}

export function useKeyboardNavigation({
  itemCount,
  onActivate,
  onNumberKeyActivate,
  focusOptions = { wrap: true, skipDisabled: false, announceChanges: true }
}: UseKeyboardNavigationProps) {
  const [state, setState] = useState<KeyboardNavigationState>({
    selectedIndex: -1,
    isKeyboardNavigation: false,
    focusedElement: null
  });

  const containerRef = useRef<HTMLElement>(null);

  const announceToScreenReader = useCallback((message: string) => {
    if (!focusOptions.announceChanges) return;
    
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    document.body.appendChild(announcement);
    
    setTimeout(() => document.body.removeChild(announcement), 1000);
  }, [focusOptions.announceChanges]);

  const moveSelection = useCallback((direction: NavigationDirection) => {
    setState(prev => {
      let newIndex = prev.selectedIndex;
      
      if (direction === 'down' || direction === 'right') {
        newIndex = prev.selectedIndex + 1;
      } else if (direction === 'up' || direction === 'left') {
        newIndex = prev.selectedIndex - 1;
      }

      if (focusOptions.wrap) {
        if (newIndex >= itemCount) newIndex = 0;
        if (newIndex < 0) newIndex = itemCount - 1;
      } else {
        newIndex = Math.max(0, Math.min(itemCount - 1, newIndex));
      }

      return {
        ...prev,
        selectedIndex: newIndex,
        isKeyboardNavigation: true
      };
    });
  }, [itemCount, focusOptions.wrap]);

  const resetSelection = useCallback(() => {
    setState(prev => ({
      ...prev,
      selectedIndex: -1,
      isKeyboardNavigation: false,
      focusedElement: null
    }));
  }, []);

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    switch (event.key) {
      case 'ArrowDown':
      case 'ArrowRight':
        event.preventDefault();
        moveSelection('down');
        break;
      case 'ArrowUp':
      case 'ArrowLeft':
        event.preventDefault();
        moveSelection('up');
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        if (state.selectedIndex >= 0) {
          onActivate(state.selectedIndex);
        }
        break;
      case 'Escape':
        event.preventDefault();
        resetSelection();
        break;
      case '1':
      case '2':
      case '3':
        event.preventDefault();
        if (onNumberKeyActivate) {
          onNumberKeyActivate(event.key);
        }
        break;
    }
  }, [state.selectedIndex, moveSelection, onActivate, onNumberKeyActivate, resetSelection]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return {
    selectedIndex: state.selectedIndex,
    isKeyboardNavigation: state.isKeyboardNavigation,
    containerRef,
    resetSelection,
    announceToScreenReader
  };
}
