import { describe, it, expect } from 'vitest';
import { MENU_OPTIONS } from './menu';

describe('MENU_OPTIONS', () => {
  it('contains the expected number of options', () => {
    expect(MENU_OPTIONS).toHaveLength(2);
  });

  it('has portfolio as the first option', () => {
    expect(MENU_OPTIONS[0].id).toBe('portfolio');
    expect(MENU_OPTIONS[0].label).toBe('Portfolio');
    expect(MENU_OPTIONS[0].shortcut).toBe('1');
    expect(MENU_OPTIONS[0].route).toBe('/portfolio-inquiry');
  });

  it('has history as the second option', () => {
    expect(MENU_OPTIONS[1].id).toBe('history');
    expect(MENU_OPTIONS[1].label).toBe('History');
    expect(MENU_OPTIONS[1].shortcut).toBe('2');
    expect(MENU_OPTIONS[1].route).toBe('/transaction-history');
  });

  it('all options have required fields', () => {
    for (const option of MENU_OPTIONS) {
      expect(option.id).toBeDefined();
      expect(option.label).toBeDefined();
      expect(option.shortcut).toBeDefined();
      expect(option.description).toBeDefined();
    }
  });

  it('all options have descriptions', () => {
    for (const option of MENU_OPTIONS) {
      expect(option.description.length).toBeGreaterThan(0);
    }
  });

  it('shortcuts are unique', () => {
    const shortcuts = MENU_OPTIONS.map(o => o.shortcut);
    expect(new Set(shortcuts).size).toBe(shortcuts.length);
  });

  it('ids are unique', () => {
    const ids = MENU_OPTIONS.map(o => o.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
});
