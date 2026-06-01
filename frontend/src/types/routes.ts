export const ROUTES = {
  MAIN_MENU: '/',
  LOGIN: '/login',
  PORTFOLIO_VIEW: '/portfolios/:id',
  TRANSACTION_HISTORY: '/portfolios/:id/history',
} as const;

export function portfolioPath(id: string): string {
  return `/portfolios/${id}`;
}

export function historyPath(id: string): string {
  return `/portfolios/${id}/history`;
}
