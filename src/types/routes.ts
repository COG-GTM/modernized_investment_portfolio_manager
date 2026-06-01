export const ROUTES = {
  MAIN_MENU: '/',
  PORTFOLIO_INQUIRY: '/portfolio-inquiry',
  TRANSACTION_HISTORY: '/transaction-history',
  TRANSACTION_SUBMIT: '/transaction-submit',
  TRANSACTION_STATUS: '/transaction-status',
} as const;

export type RouteType = typeof ROUTES[keyof typeof ROUTES];
