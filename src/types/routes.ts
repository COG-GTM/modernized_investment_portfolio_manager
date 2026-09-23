export const ROUTES = {
  MAIN_MENU: '/',
  PORTFOLIO_INQUIRY: '/portfolio-inquiry',
  TRANSACTION_HISTORY: '/transaction-history',
  BATCH_COMPLETIONS: '/batch-completions',
} as const;

export type RouteType = typeof ROUTES[keyof typeof ROUTES];
