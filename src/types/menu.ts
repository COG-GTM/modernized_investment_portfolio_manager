import { z } from 'zod';

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
    route: '/portfolio-inquiry'
  },
  {
    id: 'history',
    label: 'Transaction History',
    shortcut: '2',
    description: 'Review your investment transaction history and activity',
    route: '/transaction-history'
  },
  {
    id: 'exit',
    label: 'Exit',
    shortcut: '3',
    description: 'Return to main menu',
    route: '/'
  }
];

export const menuOptionSchema = z
  .string()
  .length(1, 'Please enter a single digit')
  .regex(/^[1-3]$/, 'Please enter 1, 2, or 3');

export const menuFormSchema = z.object({
  option: menuOptionSchema,
});

export type MenuFormData = z.infer<typeof menuFormSchema>;
