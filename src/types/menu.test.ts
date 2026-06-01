import { describe, it, expect } from 'vitest';
import { MENU_OPTIONS } from './menu';

describe('MENU_OPTIONS', () => {
  it('has 2 menu options', () => {
    expect(MENU_OPTIONS).toHaveLength(2);
  });

  it('has portfolio option as first item', () => {
    const portfolio = MENU_OPTIONS[0];
    expect(portfolio.id).toBe('portfolio');
    expect(portfolio.label).toBe('Portfolio');
    expect(portfolio.shortcut).toBe('1');
    expect(portfolio.route).toBe('/portfolio-inquiry');
    expect(portfolio.description).toBeTruthy();
  });

  it('has history option as second item', () => {
    const history = MENU_OPTIONS[1];
    expect(history.id).toBe('history');
    expect(history.label).toBe('History');
    expect(history.shortcut).toBe('2');
    expect(history.route).toBe('/transaction-history');
    expect(history.description).toBeTruthy();
  });

  it('each option has required fields', () => {
    for (const option of MENU_OPTIONS) {
      expect(option.id).toBeDefined();
      expect(option.label).toBeDefined();
      expect(option.shortcut).toBeDefined();
      expect(option.description).toBeDefined();
      expect(option.route).toBeDefined();
    }
  });
});
