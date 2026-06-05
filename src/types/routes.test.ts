import { describe, it, expect } from 'vitest';
import { ROUTES } from './routes';

describe('ROUTES', () => {
  it('has MAIN_MENU route', () => {
    expect(ROUTES.MAIN_MENU).toBeDefined();
    expect(typeof ROUTES.MAIN_MENU).toBe('string');
  });

  it('has PORTFOLIO_INQUIRY route', () => {
    expect(ROUTES.PORTFOLIO_INQUIRY).toBeDefined();
  });

  it('has TRANSACTION_HISTORY route', () => {
    expect(ROUTES.TRANSACTION_HISTORY).toBeDefined();
  });

  it('MAIN_MENU is root path', () => {
    expect(ROUTES.MAIN_MENU).toBe('/');
  });
});
