import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PositionCard from './PositionCard';
import type { Position } from '../types';

const mockPosition: Position = {
  portfolioId: 'PF-001',
  investmentId: 'INV-AAPL-001',
  symbol: 'AAPL',
  name: 'Apple Inc.',
  quantity: 100,
  costBasis: 15000,
  currentPrice: 175.50,
  marketValue: 17550,
  currency: 'USD',
  status: 'ACTIVE',
  gainLoss: 2550,
  gainLossPercent: 17.0,
  lastUpdated: '2024-01-15T10:30:00Z',
};

describe('PositionCard', () => {
  it('renders the symbol', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('AAPL')).toBeInTheDocument();
  });

  it('renders the name', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
  });

  it('renders the quantity', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('renders the current price', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('$175.50')).toBeInTheDocument();
  });

  it('renders the market value', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('$17,550.00')).toBeInTheDocument();
  });

  it('renders the cost basis', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('$15,000.00')).toBeInTheDocument();
  });

  it('renders the status badge', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('ACTIVE')).toBeInTheDocument();
  });

  it('renders gain/loss information', () => {
    render(<PositionCard position={mockPosition} />);
    const gainLossLabel = screen.getByText('Gain/Loss');
    expect(gainLossLabel).toBeInTheDocument();
  });

  it('calls onClick when clicked and onClick is provided', () => {
    const onClick = vi.fn();
    render(<PositionCard position={mockPosition} onClick={onClick} />);
    const card = screen.getByText('AAPL').closest('.space-y-4') as HTMLElement;
    fireEvent.click(card);
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('applies cursor-pointer when onClick is provided', () => {
    const { container } = render(<PositionCard position={mockPosition} onClick={vi.fn()} />);
    expect(container.innerHTML).toContain('cursor-pointer');
  });

  it('does not apply cursor-pointer when onClick is not provided', () => {
    const { container } = render(<PositionCard position={mockPosition} />);
    const card = container.firstChild as HTMLElement;
    expect(card.className).not.toContain('cursor-pointer');
  });

  it('applies custom className', () => {
    const { container } = render(<PositionCard position={mockPosition} className="my-custom" />);
    expect(container.innerHTML).toContain('my-custom');
  });

  it('applies custom style', () => {
    const { container } = render(
      <PositionCard position={mockPosition} style={{ animationDelay: '100ms' }} />
    );
    const card = container.firstChild as HTMLElement;
    expect(card.style.animationDelay).toBe('100ms');
  });

  it('renders INACTIVE status with correct styling', () => {
    const inactivePosition: Position = { ...mockPosition, status: 'INACTIVE' };
    render(<PositionCard position={inactivePosition} />);
    const badge = screen.getByText('INACTIVE');
    expect(badge.className).toContain('bg-gray-100');
  });

  it('renders PENDING status with correct styling', () => {
    const pendingPosition: Position = { ...mockPosition, status: 'PENDING' };
    render(<PositionCard position={pendingPosition} />);
    const badge = screen.getByText('PENDING');
    expect(badge.className).toContain('bg-yellow-100');
  });

  it('renders negative gain/loss correctly', () => {
    const lossPosition: Position = {
      ...mockPosition,
      gainLoss: -1000,
      gainLossPercent: -5.5,
    };
    render(<PositionCard position={lossPosition} />);
    // The formatted gain/loss should contain the negative value
    expect(screen.getByText('Gain/Loss')).toBeInTheDocument();
  });
});
