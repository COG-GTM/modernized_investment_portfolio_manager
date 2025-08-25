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

export type MenuOptionId = 'portfolio' | 'history' | 'reports' | 'admin' | 'audit' | 'help' | 'exit';

export const MENU_OPTIONS: MenuOption[] = [
  {
    id: 'portfolio',
    label: 'Portfolio Positions',
    shortcut: '1',
    description: 'View real-time account data and investment portfolio holdings',
    route: '/portfolio-inquiry'
  },
  {
    id: 'history',
    label: 'Transaction History',
    shortcut: '2',
    description: 'Review historical investment transactions and activity lookups',
    route: '/transaction-history'
  },
  {
    id: 'reports',
    label: 'Reports & Analytics',
    shortcut: '3',
    description: 'Access business intelligence reports and portfolio analytics',
    route: '/reports-analytics'
  },
  {
    id: 'admin',
    label: 'System Administration',
    shortcut: '4',
    description: 'Manage user accounts, permissions, and system settings',
    route: '/system-administration'
  },
  {
    id: 'audit',
    label: 'Audit & Compliance',
    shortcut: '5',
    description: 'View security logs, compliance reports, and audit trails',
    route: '/audit-compliance'
  },
  {
    id: 'help',
    label: 'Help & Documentation',
    shortcut: '6',
    description: 'Access user guides, documentation, and support resources',
    route: '/help-documentation'
  },
  {
    id: 'exit',
    label: 'Exit',
    shortcut: '7',
    description: 'Exit the application',
    action: () => {
      if (window.confirm('Are you sure you want to exit the application?')) {
        window.close();
      }
    }
  }
];
