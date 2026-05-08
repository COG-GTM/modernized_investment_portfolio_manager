export const ROUTES = {
  MAIN_MENU: '/',
  PORTFOLIO_INQUIRY: '/portfolio-inquiry',
  TRANSACTION_HISTORY: '/transaction-history',
  ONLINE_INQUIRY: '/online-inquiry',
} as const;

export type RouteType = typeof ROUTES[keyof typeof ROUTES];
