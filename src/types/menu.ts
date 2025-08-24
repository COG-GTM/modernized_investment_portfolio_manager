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
    label: 'Portfolio',
    shortcut: '1',
    description: 'View and analyze your investment portfolio holdings and performance',
    route: '/portfolio-inquiry'
  },
  {
    id: 'history',
    label: 'History',
    shortcut: '2',
    description: 'Review your investment transaction history and activity',
    route: '/transaction-history'
  },
  {
    id: 'exit',
    label: 'Exit',
    shortcut: '3',
    description: 'Exit the application',
    action: () => {
      if (window.confirm('Are you sure you want to exit the application?')) {
        window.close();
      }
    }
  }
];
