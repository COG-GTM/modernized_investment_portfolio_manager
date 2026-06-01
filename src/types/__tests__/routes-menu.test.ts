import { describe, it, expect } from 'vitest';
import { ROUTES } from '../routes';
import { MENU_OPTIONS } from '../menu';

describe('ROUTES', () => {
  it('has a MAIN_MENU route at /', () => {
    expect(ROUTES.MAIN_MENU).toBe('/');
  });

  it('has a PORTFOLIO_INQUIRY route', () => {
    expect(ROUTES.PORTFOLIO_INQUIRY).toBe('/portfolio-inquiry');
  });

  it('has a TRANSACTION_HISTORY route', () => {
    expect(ROUTES.TRANSACTION_HISTORY).toBe('/transaction-history');
  });

  it('has exactly 3 routes', () => {
    expect(Object.keys(ROUTES)).toHaveLength(3);
  });
});

describe('MENU_OPTIONS', () => {
  it('contains 2 menu options', () => {
    expect(MENU_OPTIONS).toHaveLength(2);
  });

  it('has a portfolio option with correct properties', () => {
    const portfolio = MENU_OPTIONS.find(opt => opt.id === 'portfolio');
    expect(portfolio).toBeDefined();
    expect(portfolio!.label).toBe('Portfolio');
    expect(portfolio!.shortcut).toBe('1');
    expect(portfolio!.route).toBe('/portfolio-inquiry');
    expect(portfolio!.description).toBeTruthy();
  });

  it('has a history option with correct properties', () => {
    const history = MENU_OPTIONS.find(opt => opt.id === 'history');
    expect(history).toBeDefined();
    expect(history!.label).toBe('History');
    expect(history!.shortcut).toBe('2');
    expect(history!.route).toBe('/transaction-history');
    expect(history!.description).toBeTruthy();
  });

  it('all options have required fields', () => {
    for (const option of MENU_OPTIONS) {
      expect(option.id).toBeTruthy();
      expect(option.label).toBeTruthy();
      expect(option.shortcut).toBeTruthy();
      expect(option.description).toBeTruthy();
    }
  });

  it('menu option shortcuts are unique', () => {
    const shortcuts = MENU_OPTIONS.map(opt => opt.shortcut);
    const uniqueShortcuts = new Set(shortcuts);
    expect(uniqueShortcuts.size).toBe(shortcuts.length);
  });

  it('menu option ids are unique', () => {
    const ids = MENU_OPTIONS.map(opt => opt.id);
    const uniqueIds = new Set(ids);
    expect(uniqueIds.size).toBe(ids.length);
  });
});
