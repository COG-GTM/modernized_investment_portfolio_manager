import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import MenuOption from './MenuOption';
import type { MenuOption as MenuOptionType } from '../types/menu';

const mockOption: MenuOptionType = {
  id: 'portfolio',
  label: 'Portfolio',
  shortcut: '1',
  description: 'View your portfolio',
  route: '/portfolio-inquiry',
};

const mockOptionNoRoute: MenuOptionType = {
  id: 'test',
  label: 'Test',
  shortcut: '3',
  description: 'Test option',
};

function renderMenuOption(props: Partial<Parameters<typeof MenuOption>[0]> = {}) {
  return render(
    <MemoryRouter>
      <MenuOption
        option={mockOption}
        index={0}
        isSelected={false}
        isKeyboardSelected={false}
        onSelect={() => {}}
        onKeyPress={() => {}}
        {...props}
      />
    </MemoryRouter>
  );
}

describe('MenuOption', () => {
  it('renders option label', () => {
    renderMenuOption();
    expect(screen.getByText('Portfolio')).toBeInTheDocument();
  });

  it('renders description', () => {
    renderMenuOption();
    expect(screen.getByText('View your portfolio')).toBeInTheDocument();
  });

  it('renders shortcut key', () => {
    renderMenuOption();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('calls onSelect on click', () => {
    const onSelect = vi.fn();
    renderMenuOption({ onSelect });
    fireEvent.click(screen.getByRole('button'));
    expect(onSelect).toHaveBeenCalledWith('portfolio');
  });

  it('calls onKeyPress on Enter', () => {
    const onKeyPress = vi.fn();
    renderMenuOption({ onKeyPress });
    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' });
    expect(onKeyPress).toHaveBeenCalledWith('portfolio');
  });

  it('calls onKeyPress on Space', () => {
    const onKeyPress = vi.fn();
    renderMenuOption({ onKeyPress });
    fireEvent.keyDown(screen.getByRole('button'), { key: ' ' });
    expect(onKeyPress).toHaveBeenCalledWith('portfolio');
  });

  it('applies selected styling', () => {
    const { container } = renderMenuOption({ isSelected: true });
    expect(container.innerHTML).toContain('border-primary');
  });

  it('applies keyboard selected styling', () => {
    const { container } = renderMenuOption({ isKeyboardSelected: true });
    expect(container.innerHTML).toContain('ring-primary');
  });

  it('has button role', () => {
    renderMenuOption();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('wraps in Link when route exists', () => {
    renderMenuOption();
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/portfolio-inquiry');
  });

  it('renders without Link when no route', () => {
    render(
      <MemoryRouter>
        <MenuOption
          option={mockOptionNoRoute}
          index={2}
          isSelected={false}
          isKeyboardSelected={false}
          onSelect={() => {}}
          onKeyPress={() => {}}
        />
      </MemoryRouter>
    );
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });

  it('calls option.action when action exists', () => {
    const action = vi.fn();
    const optionWithAction = { ...mockOptionNoRoute, action };
    render(
      <MemoryRouter>
        <MenuOption
          option={optionWithAction}
          index={2}
          isSelected={false}
          isKeyboardSelected={false}
          onSelect={() => {}}
          onKeyPress={() => {}}
        />
      </MemoryRouter>
    );
    fireEvent.click(screen.getByRole('button'));
    expect(action).toHaveBeenCalledOnce();
  });
});
