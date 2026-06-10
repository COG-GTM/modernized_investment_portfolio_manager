import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import MenuOption from '../../components/MenuOption';
import type { MenuOption as MenuOptionType } from '../../types/menu';

const routeOption: MenuOptionType = {
  id: 'portfolio',
  label: 'Portfolio',
  shortcut: '1',
  description: 'View portfolio',
  route: '/portfolio-inquiry',
};

const actionOption: MenuOptionType = {
  id: 'exit',
  label: 'Exit',
  shortcut: '3',
  description: 'Exit the application',
  action: vi.fn(),
};

const renderMenuOption = (option: MenuOptionType, overrides = {}) => {
  const defaultProps = {
    option,
    isSelected: false,
    isKeyboardSelected: false,
    index: 0,
    onSelect: vi.fn(),
    onKeyPress: vi.fn(),
    ...overrides,
  };
  return render(
    <MemoryRouter>
      <MenuOption {...defaultProps} />
    </MemoryRouter>
  );
};

describe('MenuOption', () => {
  it('renders label and description', () => {
    renderMenuOption(routeOption);
    expect(screen.getByText('Portfolio')).toBeInTheDocument();
    expect(screen.getByText('View portfolio')).toBeInTheDocument();
  });

  it('renders shortcut badge', () => {
    renderMenuOption(routeOption);
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('wraps in Link for route options', () => {
    const { container } = renderMenuOption(routeOption);
    const link = container.querySelector('a');
    expect(link).toBeInTheDocument();
    expect(link?.getAttribute('href')).toBe('/portfolio-inquiry');
  });

  it('calls action on click for action options', () => {
    renderMenuOption(actionOption);
    fireEvent.click(screen.getByText('Exit'));
    expect(actionOption.action).toHaveBeenCalled();
  });

  it('calls onKeyPress on Enter', () => {
    const onKeyPress = vi.fn();
    renderMenuOption(routeOption, { onKeyPress });
    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' });
    expect(onKeyPress).toHaveBeenCalledWith('portfolio');
  });

  it('calls onKeyPress on Space', () => {
    const onKeyPress = vi.fn();
    renderMenuOption(routeOption, { onKeyPress });
    fireEvent.keyDown(screen.getByRole('button'), { key: ' ' });
    expect(onKeyPress).toHaveBeenCalledWith('portfolio');
  });

  it('applies selected styles', () => {
    renderMenuOption(routeOption, { isSelected: true });
    const btn = screen.getByRole('button');
    expect(btn.className).toContain('border-primary');
  });

  it('applies keyboard selected styles', () => {
    renderMenuOption(routeOption, { isKeyboardSelected: true });
    const btn = screen.getByRole('button');
    expect(btn.className).toContain('ring-2');
  });

  it('has correct aria attributes', () => {
    renderMenuOption(routeOption, { isSelected: true });
    const btn = screen.getByRole('button');
    expect(btn).toHaveAttribute('aria-pressed', 'true');
  });
});
