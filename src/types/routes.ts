export const ROUTES = {
  MAIN_MENU: '/',
  PORTFOLIO_INQUIRY: '/portfolio-inquiry',
  TRANSACTION_HISTORY: '/transaction-history',
  PORTFOLIO_TRANSFER: '/portfolio-transfer',
} as const;

export type RouteType = typeof ROUTES[keyof typeof ROUTES];
