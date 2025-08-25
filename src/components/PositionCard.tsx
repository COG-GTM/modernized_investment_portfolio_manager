import React from 'react';
import Card from './Card';
import { Position } from '../types';
import { formatCurrency, formatNumber, formatGainLoss } from '../utils/format';

interface PositionCardProps {
  position: Position;
  onClick?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

export default function PositionCard({ position, onClick, className = '', style }: PositionCardProps) {
  const { formatted: gainLossFormatted, colorClass: gainLossColor } = formatGainLoss(
    position.gainLoss,
    position.gainLossPercent,
    position.currency
  );

  const isClickable = !!onClick;

  return (
    <Card 
      hover={isClickable}
      className={`${className} ${isClickable ? 'cursor-pointer' : ''}`}
      style={style}
    >
      <div className="space-y-4" onClick={onClick}>
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-semibold">{position.symbol}</h3>
            <p className="text-sm text-muted-foreground">{position.name}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-muted-foreground">Status</p>
            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
              position.status === 'ACTIVE' 
                ? 'bg-green-100 text-green-800' 
                : position.status === 'INACTIVE'
                ? 'bg-gray-100 text-gray-800'
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {position.status}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Quantity</p>
            <p className="font-medium">{formatNumber(position.quantity, 0)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Current Price</p>
            <p className="font-medium">{formatCurrency(position.currentPrice, position.currency)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Market Value</p>
            <p className="font-medium">{formatCurrency(position.marketValue, position.currency)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Cost Basis</p>
            <p className="font-medium">{formatCurrency(position.costBasis, position.currency)}</p>
          </div>
        </div>

        <div className="pt-2 border-t">
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted-foreground">Gain/Loss</span>
            <span className={`font-semibold ${gainLossColor}`}>
              {gainLossFormatted}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
}
