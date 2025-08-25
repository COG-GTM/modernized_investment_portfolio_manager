
interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  padding?: 'sm' | 'md' | 'lg';
}

export default function Card({ children, className = '', hover = false, padding = 'md' }: CardProps) {
  const paddingClasses = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8'
  };

  const hoverClasses = hover ? 'hover:shadow-lg hover:-translate-y-1 transition-smooth cursor-pointer' : '';

  return (
    <div className={`bg-card border border-border rounded-lg shadow-sm ${paddingClasses[padding]} ${hoverClasses} ${className}`}>
      {children}
    </div>
  );
}
