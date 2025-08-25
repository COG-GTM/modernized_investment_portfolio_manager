
interface PageHeaderProps {
  title: string;
  subtitle?: string;
  className?: string;
}

export default function PageHeader({ title, subtitle, className = '' }: PageHeaderProps) {
  return (
    <header className={`text-center space-y-4 animate-fade-in ${className}`}>
      <h1 className="text-4xl font-bold text-primary">
        {title}
      </h1>
      {subtitle && (
        <p className="text-lg text-muted-foreground">
          {subtitle}
        </p>
      )}
    </header>
  );
}
