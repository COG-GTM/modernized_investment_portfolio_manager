import { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { MENU_OPTIONS, MenuState } from '../types/menu';
import { useKeyboardNavigation } from '../hooks/useKeyboardNavigation';
import MenuOption from '../components/MenuOption';
import { Container, PageHeader } from '../components';
import { ConfirmationDialog } from '../components/dialogs';

export default function MainMenu() {
  const history = useHistory();
  const [menuState, setMenuState] = useState<MenuState>({
    selectedOption: null,
    isKeyboardNavigation: false
  });
  
  const [showExitDialog, setShowExitDialog] = useState(false);

  const handleExitRequest = () => {
    setShowExitDialog(true);
  };

  const handleExitConfirm = () => {
    setShowExitDialog(false);
    window.close();
  };

  const handleExitCancel = () => {
    setShowExitDialog(false);
  };

  const menuOptions = MENU_OPTIONS.map(option => 
    option.id === 'exit' 
      ? { ...option, action: handleExitRequest }
      : option
  );

  const handleOptionActivate = (index: number) => {
    const option = menuOptions[index];
    if (!option) return;

    setMenuState(prev => ({
      ...prev,
      selectedOption: option.id,
      isKeyboardNavigation: true
    }));

    if (option.action) {
      setTimeout(() => option.action!(), 150);
    } else if (option.route) {
      setTimeout(() => history.push(option.route!), 150);
    }
  };

  const handleNumberKeyActivate = (key: string) => {
    const option = menuOptions.find(opt => opt.shortcut === key);
    if (option) {
      const index = menuOptions.indexOf(option);
      handleOptionActivate(index);
    }
  };

  const { selectedIndex, isKeyboardNavigation, containerRef } = useKeyboardNavigation({
    itemCount: menuOptions.length,
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
    const option = menuOptions.find(opt => opt.id === optionId);
    const index = option ? menuOptions.indexOf(option) : -1;
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
              {menuOptions.map((option, index) => (
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
                <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono shadow-sm">2</kbd>, 
                <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono shadow-sm">3</kbd>. 
                Press <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono shadow-sm">Enter</kbd> to select, 
                <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono shadow-sm">Esc</kbd> to reset.
              </p>
            </div>
          </main>
        </div>
      </Container>

      <ConfirmationDialog
        isOpen={showExitDialog}
        title="Exit Application"
        message="Are you sure you want to exit the Portfolio Management System?"
        onConfirm={handleExitConfirm}
        onCancel={handleExitCancel}
      />
    </div>
  );
}
