export const ROUTES = {
  MAIN_MENU: '/',
  PORTFOLIO_INQUIRY: '/portfolio-inquiry',
  TRANSACTION_HISTORY: '/transaction-history',
  VISITORS_HISTORY: '/visitors-history',
} as const;

export type RouteType = typeof ROUTES[keyof typeof ROUTES];
