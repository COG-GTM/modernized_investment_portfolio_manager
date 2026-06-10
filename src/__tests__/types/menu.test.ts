import { describe, it, expect } from 'vitest';
import { MENU_OPTIONS } from '../../types/menu';

describe('MENU_OPTIONS', () => {
  it('has exactly 2 options', () => {
    expect(MENU_OPTIONS).toHaveLength(2);
  });

  it('first option is portfolio', () => {
    expect(MENU_OPTIONS[0].id).toBe('portfolio');
    expect(MENU_OPTIONS[0].shortcut).toBe('1');
    expect(MENU_OPTIONS[0].route).toBe('/portfolio-inquiry');
  });

  it('second option is history', () => {
    expect(MENU_OPTIONS[1].id).toBe('history');
    expect(MENU_OPTIONS[1].shortcut).toBe('2');
    expect(MENU_OPTIONS[1].route).toBe('/transaction-history');
  });

  it('all options have required fields', () => {
    MENU_OPTIONS.forEach((option) => {
      expect(option.id).toBeTruthy();
      expect(option.label).toBeTruthy();
      expect(option.shortcut).toBeTruthy();
      expect(option.description).toBeTruthy();
    });
  });
});
