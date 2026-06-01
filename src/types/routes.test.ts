import { describe, it, expect } from 'vitest';
import { ROUTES } from './routes';

describe('ROUTES', () => {
  it('has MAIN_MENU route', () => {
    expect(ROUTES.MAIN_MENU).toBe('/');
  });

  it('has PORTFOLIO_INQUIRY route', () => {
    expect(ROUTES.PORTFOLIO_INQUIRY).toBe('/portfolio-inquiry');
  });

  it('has TRANSACTION_HISTORY route', () => {
    expect(ROUTES.TRANSACTION_HISTORY).toBe('/transaction-history');
  });

  it('has exactly 3 routes', () => {
    expect(Object.keys(ROUTES)).toHaveLength(3);
  });
});
