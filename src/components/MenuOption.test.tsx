import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import MenuOption from './MenuOption';
import type { MenuOption as MenuOptionType } from '../types/menu';

const defaultOption: MenuOptionType = {
  id: 'portfolio',
  label: 'Portfolio',
  shortcut: '1',
  description: 'View your portfolio',
  route: '/portfolio-inquiry',
};

const renderWithRouter = (ui: React.ReactElement) => {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
};

describe('MenuOption', () => {
  it('renders the option label', () => {
    renderWithRouter(
      <MenuOption
        option={defaultOption}
        isSelected={false}
        index={0}
        onSelect={vi.fn()}
        onKeyPress={vi.fn()}
      />
    );
    expect(screen.getByText('Portfolio')).toBeInTheDocument();
  });

  it('renders the description', () => {
    renderWithRouter(
      <MenuOption
        option={defaultOption}
        isSelected={false}
        index={0}
        onSelect={vi.fn()}
        onKeyPress={vi.fn()}
      />
    );
    expect(screen.getByText('View your portfolio')).toBeInTheDocument();
  });

  it('renders the shortcut', () => {
    renderWithRouter(
      <MenuOption
        option={defaultOption}
        isSelected={false}
        index={0}
        onSelect={vi.fn()}
        onKeyPress={vi.fn()}
      />
    );
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('wraps in a Link when route is provided', () => {
    renderWithRouter(
      <MenuOption
        option={defaultOption}
        isSelected={false}
        index={0}
        onSelect={vi.fn()}
        onKeyPress={vi.fn()}
      />
    );
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/portfolio-inquiry');
  });

  it('does not wrap in a Link when route is not provided', () => {
    const optionWithoutRoute: MenuOptionType = {
      ...defaultOption,
      route: undefined,
    };
    renderWithRouter(
      <MenuOption
        option={optionWithoutRoute}
        isSelected={false}
        index={0}
        onSelect={vi.fn()}
        onKeyPress={vi.fn()}
      />
    );
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });

  it('calls onSelect when clicked without action', () => {
    const onSelect = vi.fn();
    renderWithRouter(
      <MenuOption
        option={defaultOption}
        isSelected={false}
        index={0}
        onSelect={onSelect}
        onKeyPress={vi.fn()}
      />
    );
    fireEvent.click(screen.getByRole('button'));
    expect(onSelect).toHaveBeenCalledWith('portfolio');
  });

  it('calls option.action when clicked and action exists', () => {
    const action = vi.fn();
    const optionWithAction: MenuOptionType = {
      ...defaultOption,
      route: undefined,
      action,
    };
    renderWithRouter(
      <MenuOption
        option={optionWithAction}
        isSelected={false}
        index={0}
        onSelect={vi.fn()}
        onKeyPress={vi.fn()}
      />
    );
    fireEvent.click(screen.getByRole('button'));
    expect(action).toHaveBeenCalled();
  });

  it('calls onKeyPress on Enter key', () => {
    const onKeyPress = vi.fn();
    renderWithRouter(
      <MenuOption
        option={defaultOption}
        isSelected={false}
        index={0}
        onSelect={vi.fn()}
        onKeyPress={onKeyPress}
      />
    );
    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' });
    expect(onKeyPress).toHaveBeenCalledWith('portfolio');
  });

  it('calls onKeyPress on Space key', () => {
    const onKeyPress = vi.fn();
    renderWithRouter(
      <MenuOption
        option={defaultOption}
        isSelected={false}
        index={0}
        onSelect={vi.fn()}
        onKeyPress={onKeyPress}
      />
    );
    fireEvent.keyDown(screen.getByRole('button'), { key: ' ' });
    expect(onKeyPress).toHaveBeenCalledWith('portfolio');
  });

  it('applies selected styles when isSelected is true', () => {
    renderWithRouter(
      <MenuOption
        option={defaultOption}
        isSelected={true}
        index={0}
        onSelect={vi.fn()}
        onKeyPress={vi.fn()}
      />
    );
    const button = screen.getByRole('button');
    expect(button.className).toContain('border-primary');
    expect(button.getAttribute('aria-pressed')).toBe('true');
  });

  it('applies keyboard selected styles', () => {
    renderWithRouter(
      <MenuOption
        option={defaultOption}
        isSelected={false}
        isKeyboardSelected={true}
        index={0}
        onSelect={vi.fn()}
        onKeyPress={vi.fn()}
      />
    );
    const button = screen.getByRole('button');
    expect(button.getAttribute('aria-current')).toBe('true');
  });

  it('has correct aria-label', () => {
    renderWithRouter(
      <MenuOption
        option={defaultOption}
        isSelected={false}
        index={0}
        onSelect={vi.fn()}
        onKeyPress={vi.fn()}
      />
    );
    const button = screen.getByRole('button');
    expect(button.getAttribute('aria-label')).toContain('Portfolio');
    expect(button.getAttribute('aria-label')).toContain('Press 1');
  });
});
