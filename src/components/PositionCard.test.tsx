import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PositionCard from './PositionCard';
import type { Position } from '../types';

const mockPosition: Position = {
  portfolioId: 'PORT0001',
  investmentId: 'AAPL123456',
  symbol: 'AAPL',
  name: 'Apple Inc.',
  quantity: 100,
  costBasis: 15000,
  currentPrice: 185,
  marketValue: 18500,
  currency: 'USD',
  status: 'ACTIVE',
  gainLoss: 3500,
  gainLossPercent: 23.33,
  lastUpdated: '2024-06-01',
};

describe('PositionCard', () => {
  it('renders symbol', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('AAPL')).toBeInTheDocument();
  });

  it('renders name', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
  });

  it('renders status badge', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('ACTIVE')).toBeInTheDocument();
  });

  it('renders quantity label', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('Quantity')).toBeInTheDocument();
  });

  it('renders current price label', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('Current Price')).toBeInTheDocument();
  });

  it('renders market value label', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('Market Value')).toBeInTheDocument();
  });

  it('renders cost basis label', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('Cost Basis')).toBeInTheDocument();
  });

  it('renders gain/loss label', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('Gain/Loss')).toBeInTheDocument();
  });

  it('applies green styling for positive gain', () => {
    const { container } = render(<PositionCard position={mockPosition} />);
    expect(container.innerHTML).toContain('text-green-600');
  });

  it('applies red styling for negative gain', () => {
    const negPos = { ...mockPosition, gainLoss: -1000, gainLossPercent: -5.0 };
    const { container } = render(<PositionCard position={negPos} />);
    expect(container.innerHTML).toContain('text-red-600');
  });

  it('is clickable when onClick provided', () => {
    const onClick = vi.fn();
    render(<PositionCard position={mockPosition} onClick={onClick} />);
    const card = screen.getByText('AAPL').closest('.space-y-4')!;
    fireEvent.click(card);
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('has cursor-pointer when clickable', () => {
    const { container } = render(
      <PositionCard position={mockPosition} onClick={() => {}} />
    );
    expect(container.innerHTML).toContain('cursor-pointer');
  });

  it('does not have cursor-pointer when not clickable', () => {
    const { container } = render(<PositionCard position={mockPosition} />);
    expect(container.innerHTML).not.toContain('cursor-pointer');
  });

  it('renders INACTIVE status with gray styling', () => {
    const inactivePos = { ...mockPosition, status: 'INACTIVE' as const };
    const { container } = render(<PositionCard position={inactivePos} />);
    expect(container.innerHTML).toContain('bg-gray-100');
  });

  it('renders PENDING status with yellow styling', () => {
    const pendingPos = { ...mockPosition, status: 'PENDING' as const };
    const { container } = render(<PositionCard position={pendingPos} />);
    expect(container.innerHTML).toContain('bg-yellow-100');
  });

  it('renders ACTIVE status with green styling', () => {
    const { container } = render(<PositionCard position={mockPosition} />);
    expect(container.innerHTML).toContain('bg-green-100');
  });

  it('applies custom className', () => {
    const { container } = render(
      <PositionCard position={mockPosition} className="extra" />
    );
    expect(container.innerHTML).toContain('extra');
  });
});
