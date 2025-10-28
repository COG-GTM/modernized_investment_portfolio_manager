export const ROUTES = {
  MAIN_MENU: '/',
  PORTFOLIO_INQUIRY: '/portfolio-inquiry',
  TRANSACTION_HISTORY: '/transaction-history',
  PORTFOLIO: '/portfolio',
  HISTORY: '/history',
} as const;

export type RouteType = typeof ROUTES[keyof typeof ROUTES];
