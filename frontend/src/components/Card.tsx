import type { ReactNode, CSSProperties } from 'react';
import { cn } from '../utils/format';

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  padding?: 'sm' | 'md' | 'lg';
  style?: CSSProperties;
}

const paddingClasses = {
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export default function Card({ children, className, hover = false, padding = 'md', style }: CardProps) {
  return (
    <div
      className={cn(
        'bg-card border border-border rounded-lg shadow-sm',
        paddingClasses[padding],
        hover && 'hover:shadow-lg hover:-translate-y-1 transition-smooth cursor-pointer',
        className
      )}
      style={style}
    >
      {children}
    </div>
  );
}
