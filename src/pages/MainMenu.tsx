import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MENU_OPTIONS, MenuState } from '../types/menu';
import { useKeyboardNavigation } from '../hooks/useKeyboardNavigation';
import MenuOption from '../components/MenuOption';
import { Container, PageHeader } from '../components';

export default function MainMenu() {
  const navigate = useNavigate();
  const [menuState, setMenuState] = useState<MenuState>({
    selectedOption: null,
    isKeyboardNavigation: false
  });
  

  const handleOptionActivate = (index: number) => {
    const option = MENU_OPTIONS[index];
    if (!option) return;

    setMenuState(prev => ({
      ...prev,
      selectedOption: option.id,
      isKeyboardNavigation: true
    }));

    if (option.route) {
      setTimeout(() => navigate(option.route!), 150);
    }
  };

  const handleNumberKeyActivate = (key: string) => {
    const option = MENU_OPTIONS.find(opt => opt.shortcut === key);
    if (option) {
      const index = MENU_OPTIONS.indexOf(option);
      handleOptionActivate(index);
    }
  };

  const { selectedIndex, isKeyboardNavigation, containerRef } = useKeyboardNavigation({
    itemCount: MENU_OPTIONS.length,
    onActivate: handleOptionActivate,
    onNumberKeyActivate: handleNumberKeyActivate
  });

  const handleOptionSelect = (optionId: string) => {
    setMenuState(prev => ({
      ...prev,
      selectedOption: optionId,
      isKeyboardNavigation: false
    }));
  };

  const handleOptionKeyPress = (optionId: string) => {
    const option = MENU_OPTIONS.find(opt => opt.id === optionId);
    const index = option ? MENU_OPTIONS.indexOf(option) : -1;
    if (index >= 0) {
      handleOptionActivate(index);
    }
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="md">
        <div className="space-y-12">
          <PageHeader 
            title="Investment Portfolio Manager"
            subtitle="View, analyze, and manage investment portfolios"
            className="mb-12"
          />
          
          <main 
            ref={containerRef}
            className="mx-auto"
            role="menu"
            aria-label="Main navigation menu"
          >
            <div className="grid gap-6 md:grid-cols-2 max-w-4xl mx-auto animate-slide-up">
              {MENU_OPTIONS.map((option, index) => (
                <div 
                  key={option.id}
                  className="animate-fade-in"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <MenuOption
                    option={option}
                    index={index}
                    isSelected={menuState.selectedOption === option.id}
                    isKeyboardSelected={isKeyboardNavigation && selectedIndex === index}
                    onSelect={handleOptionSelect}
                    onKeyPress={handleOptionKeyPress}
                  />
                </div>
              ))}
            </div>
            
            <div className="mt-8 text-center animate-fade-in" style={{ animationDelay: '400ms' }}>
              <p className="text-sm text-muted-foreground">
                Navigation: Use <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono shadow-sm">↑↓</kbd> arrow keys or 
                shortcuts <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono shadow-sm">1</kbd>, 
                <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono shadow-sm">2</kbd>. 
                Press <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono shadow-sm">Enter</kbd> to select, 
                <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono shadow-sm">Esc</kbd> to reset.
              </p>
            </div>
            
            {/* Fidelity Logo */}
            <div className="mt-12 flex justify-center animate-fade-in" style={{ animationDelay: '600ms' }}>
              <img 
                src="/src/assets/fidelity-logo.png"
                alt="Fidelity"
                width={120}
                height={40}
                className="opacity-80 hover:opacity-100 transition-opacity"
              />
            </div>
            
          </main>
        </div>
      </Container>

    </div>
  );
}
