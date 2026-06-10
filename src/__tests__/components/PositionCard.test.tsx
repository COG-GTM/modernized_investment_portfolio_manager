import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PositionCard from '../../components/PositionCard';
import type { Position } from '../../types';

const mockPosition: Position = {
  portfolioId: 'PF-12345',
  investmentId: 'INV-AAPL-001',
  symbol: 'AAPL',
  name: 'Apple Inc.',
  quantity: 150,
  costBasis: 25500,
  currentPrice: 185.25,
  marketValue: 27787.50,
  currency: 'USD',
  status: 'ACTIVE',
  gainLoss: 2287.50,
  gainLossPercent: 8.97,
  lastUpdated: 'June 10, 2024',
};

describe('PositionCard', () => {
  it('renders symbol and name', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
  });

  it('renders status badge', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('ACTIVE')).toBeInTheDocument();
  });

  it('renders quantity', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('150')).toBeInTheDocument();
  });

  it('renders market value', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('$27,787.50')).toBeInTheDocument();
  });

  it('renders gain/loss info', () => {
    render(<PositionCard position={mockPosition} />);
    expect(screen.getByText('Gain/Loss')).toBeInTheDocument();
  });

  it('applies cursor-pointer when onClick provided', () => {
    const { container } = render(<PositionCard position={mockPosition} onClick={vi.fn()} />);
    const card = container.querySelector('.cursor-pointer');
    expect(card).toBeInTheDocument();
  });

  it('fires onClick when clicked', () => {
    const onClick = vi.fn();
    render(<PositionCard position={mockPosition} onClick={onClick} />);
    fireEvent.click(screen.getByText('AAPL'));
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('renders INACTIVE status correctly', () => {
    const inactivePos = { ...mockPosition, status: 'INACTIVE' as const };
    render(<PositionCard position={inactivePos} />);
    expect(screen.getByText('INACTIVE')).toBeInTheDocument();
  });

  it('renders PENDING status correctly', () => {
    const pendingPos = { ...mockPosition, status: 'PENDING' as const };
    render(<PositionCard position={pendingPos} />);
    expect(screen.getByText('PENDING')).toBeInTheDocument();
  });
});
