export interface MenuOption {
  id: string;
  label: string;
  shortcut: string;
  description: string;
  route?: string;
  action?: () => void;
}

export interface MenuState {
  selectedOption: string | null;
  isKeyboardNavigation: boolean;
}

export type MenuOptionId = 'portfolio' | 'history' | 'exit';

export const MENU_OPTIONS: MenuOption[] = [
  {
    id: 'portfolio',
    label: 'Portfolio Position Inquiry',
    shortcut: '1',
    description: 'View and analyze your investment portfolio holdings and performance',
    route: '/portfolio'
  },
  {
    id: 'history',
    label: 'Transaction History',
    shortcut: '2',
    description: 'Review your investment transaction history and activity',
    route: '/history'
  },
  {
    id: 'exit',
    label: 'Exit',
    shortcut: '3',
    description: 'Exit the Portfolio Management System',
  }
];
