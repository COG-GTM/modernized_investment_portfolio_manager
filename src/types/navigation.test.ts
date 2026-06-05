import { describe, it, expect } from 'vitest';
import type {
  KeyboardNavigationState,
  NavigationDirection,
  FocusManagementOptions,
  ConfirmationDialogState,
} from './navigation';

describe('navigation types', () => {
  it('KeyboardNavigationState can be constructed', () => {
    const state: KeyboardNavigationState = {
      selectedIndex: 0,
      isKeyboardNavigation: false,
      focusedElement: null,
    };
    expect(state.selectedIndex).toBe(0);
    expect(state.isKeyboardNavigation).toBe(false);
    expect(state.focusedElement).toBeNull();
  });

  it('NavigationDirection values are valid', () => {
    const directions: NavigationDirection[] = ['up', 'down', 'left', 'right'];
    expect(directions).toHaveLength(4);
  });

  it('FocusManagementOptions can be constructed', () => {
    const options: FocusManagementOptions = {
      wrap: true,
      skipDisabled: false,
      announceChanges: true,
    };
    expect(options.wrap).toBe(true);
  });

  it('ConfirmationDialogState can be constructed', () => {
    const state: ConfirmationDialogState = {
      isOpen: true,
      title: 'Test',
      message: 'Are you sure?',
      onConfirm: () => {},
      onCancel: () => {},
    };
    expect(state.isOpen).toBe(true);
    expect(state.title).toBe('Test');
  });
});
