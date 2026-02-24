import { useNavigate } from 'react-router-dom';
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import Container from '../components/Container';
import PageHeader from '../components/PageHeader';
import Button from '../components/Button';

interface MenuOption {
  id: string;
  label: string;
  shortcut: string;
  description: string;
  path?: string;
}

const MENU_OPTIONS: MenuOption[] = [
  {
    id: 'portfolio',
    label: 'Portfolio Position Inquiry',
    shortcut: '1',
    description: 'View and analyze your investment portfolio holdings and performance',
    path: '/portfolios/lookup',
  },
  {
    id: 'history',
    label: 'Transaction History',
    shortcut: '2',
    description: 'Review your investment transaction history and activity',
    path: '/portfolios/lookup?tab=history',
  },
  {
    id: 'exit',
    label: 'Exit',
    shortcut: '3',
    description: 'Sign out and return to the login screen',
  },
];

export default function MainMenu() {
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const [selectedOption, setSelectedOption] = useState<string | null>(null);

  const handleOptionClick = useCallback((option: MenuOption) => {
    setSelectedOption(option.id);

    if (option.id === 'exit') {
      logout();
      navigate('/login');
      return;
    }

    if (option.path) {
      setTimeout(() => navigate(option.path!), 150);
    }
  }, [logout, navigate]);

  // Global keyboard shortcuts (1/2/3) matching COBOL CICS PF key behavior
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) return;
      const option = MENU_OPTIONS.find(o => o.shortcut === e.key);
      if (option) {
        handleOptionClick(option);
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, [handleOptionClick]);

  const handleKeyDown = (e: React.KeyboardEvent, option: MenuOption) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleOptionClick(option);
    }
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="md">
        <div className="space-y-12">
          <div className="flex justify-between items-start">
            <PageHeader
              title="Portfolio Management System"
              subtitle="Select an option to continue"
              className="flex-1"
            />
            {user && (
              <div className="text-sm text-muted-foreground flex items-center gap-3">
                <span>Signed in as <strong>{user.username}</strong></span>
                <Button variant="ghost" size="sm" onClick={() => { logout(); navigate('/login'); }}>
                  Sign Out
                </Button>
              </div>
            )}
          </div>

          <main role="menu" aria-label="Main navigation menu" className="mx-auto">
            <div className="grid gap-6 md:grid-cols-2 max-w-4xl mx-auto animate-slide-up">
              {MENU_OPTIONS.map((option, index) => (
                <div
                  key={option.id}
                  className="animate-fade-in"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div
                    role="menuitem"
                    tabIndex={0}
                    className={`block w-full p-6 rounded-lg border-2 transition-smooth cursor-pointer
                      focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary
                      ${selectedOption === option.id
                        ? 'border-primary bg-primary/5 shadow-xl scale-105 ring-2 ring-primary/20'
                        : 'border-border bg-card hover:border-primary/50 hover:bg-primary/5 hover:shadow-lg hover:-translate-y-1'
                      }`}
                    onClick={() => handleOptionClick(option)}
                    onKeyDown={(e) => handleKeyDown(e, option)}
                    aria-label={`${option.label} - Press ${option.shortcut} to activate`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <h2 className="text-xl font-semibold text-foreground">{option.label}</h2>
                      <span className="inline-flex items-center justify-center w-8 h-8 text-sm font-bold text-primary-foreground bg-primary rounded-full shadow-sm">
                        {option.shortcut}
                      </span>
                    </div>
                    <p className="text-muted-foreground text-sm leading-relaxed">
                      {option.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-8 text-center animate-fade-in" style={{ animationDelay: '400ms' }}>
              <p className="text-sm text-muted-foreground">
                Navigation: Use <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono shadow-sm">1</kbd>,{' '}
                <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono shadow-sm">2</kbd>,{' '}
                <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono shadow-sm">3</kbd>{' '}
                to select an option. Press <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono shadow-sm">Enter</kbd> to confirm.
              </p>
            </div>
          </main>
        </div>
      </Container>
    </div>
  );
}
