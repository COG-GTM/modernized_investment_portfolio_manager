import { describe, it, expect } from 'vitest';
import { MENU_OPTIONS } from './menu';

describe('MENU_OPTIONS', () => {
  it('is an array', () => {
    expect(Array.isArray(MENU_OPTIONS)).toBe(true);
  });

  it('has 2 items', () => {
    expect(MENU_OPTIONS).toHaveLength(2);
  });

  it('each option has required fields', () => {
    for (const option of MENU_OPTIONS) {
      expect(option).toHaveProperty('id');
      expect(option).toHaveProperty('label');
      expect(option).toHaveProperty('shortcut');
      expect(option).toHaveProperty('description');
      expect(option).toHaveProperty('route');
    }
  });

  it('includes portfolio option', () => {
    const portfolio = MENU_OPTIONS.find(o => o.id === 'portfolio');
    expect(portfolio).toBeDefined();
    expect(portfolio!.label).toBe('Portfolio');
    expect(portfolio!.shortcut).toBe('1');
    expect(portfolio!.route).toBe('/portfolio-inquiry');
  });

  it('includes history option', () => {
    const history = MENU_OPTIONS.find(o => o.id === 'history');
    expect(history).toBeDefined();
    expect(history!.label).toBe('History');
    expect(history!.shortcut).toBe('2');
    expect(history!.route).toBe('/transaction-history');
  });
});
