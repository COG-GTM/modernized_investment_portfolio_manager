import { describe, it, expect } from 'vitest';
import { ROUTES } from './routes';

describe('ROUTES', () => {
  it('has a MAIN_MENU route', () => {
    expect(ROUTES.MAIN_MENU).toBe('/');
  });

  it('has a PORTFOLIO_INQUIRY route', () => {
    expect(ROUTES.PORTFOLIO_INQUIRY).toBe('/portfolio-inquiry');
  });

  it('has a TRANSACTION_HISTORY route', () => {
    expect(ROUTES.TRANSACTION_HISTORY).toBe('/transaction-history');
  });

  it('all routes start with /', () => {
    for (const route of Object.values(ROUTES)) {
      expect(route).toMatch(/^\//);
    }
  });
});
