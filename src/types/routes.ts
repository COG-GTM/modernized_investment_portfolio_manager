export const ROUTES = {
  MAIN_MENU: '/',
  PORTFOLIO_INQUIRY: '/portfolio-inquiry',
  TRANSACTION_HISTORY: '/transaction-history',
  REPORTS_ANALYTICS: '/reports-analytics',
  SYSTEM_ADMINISTRATION: '/system-administration',
  AUDIT_COMPLIANCE: '/audit-compliance',
  HELP_DOCUMENTATION: '/help-documentation',
} as const;

export type RouteType = typeof ROUTES[keyof typeof ROUTES];
