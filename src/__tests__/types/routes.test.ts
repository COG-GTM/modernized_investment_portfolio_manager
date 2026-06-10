import { describe, it, expect } from 'vitest';
import { ROUTES } from '../../types/routes';

describe('ROUTES', () => {
  it('has main menu route', () => {
    expect(ROUTES.MAIN_MENU).toBe('/');
  });

  it('has portfolio inquiry route', () => {
    expect(ROUTES.PORTFOLIO_INQUIRY).toBe('/portfolio-inquiry');
  });

  it('has transaction history route', () => {
    expect(ROUTES.TRANSACTION_HISTORY).toBe('/transaction-history');
  });
});
