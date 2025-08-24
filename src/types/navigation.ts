export interface KeyboardNavigationState {
  selectedIndex: number;
  isKeyboardNavigation: boolean;
  focusedElement: HTMLElement | null;
}

export interface NavigationKeyEvent {
  key: string;
  preventDefault: () => void;
  target: EventTarget | null;
}

export type NavigationDirection = 'up' | 'down' | 'left' | 'right';

export interface FocusManagementOptions {
  wrap: boolean;
  skipDisabled: boolean;
  announceChanges: boolean;
}

export interface ConfirmationDialogState {
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}
