import { describe, it, expect } from 'vitest';
import { ROUTES } from './routes';

describe('ROUTES', () => {
  it('has MAIN_MENU route as /', () => {
    expect(ROUTES.MAIN_MENU).toBe('/');
  });

  it('has PORTFOLIO_INQUIRY route', () => {
    expect(ROUTES.PORTFOLIO_INQUIRY).toBe('/portfolio-inquiry');
  });

  it('has TRANSACTION_HISTORY route', () => {
    expect(ROUTES.TRANSACTION_HISTORY).toBe('/transaction-history');
  });

  it('all routes start with /', () => {
    Object.values(ROUTES).forEach((route) => {
      expect(route).toMatch(/^\//);
    });
  });
});
