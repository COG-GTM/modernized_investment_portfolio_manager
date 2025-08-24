import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MENU_OPTIONS, MenuState } from '../types/menu';
import { ConfirmationDialogState } from '../types/navigation';
import { useKeyboardNavigation } from '../hooks/useKeyboardNavigation';
import MenuOption from '../components/MenuOption';
import ConfirmationDialog from '../components/dialogs/ConfirmationDialog';

export default function MainMenu() {
  const navigate = useNavigate();
  const [menuState, setMenuState] = useState<MenuState>({
    selectedOption: null,
    isKeyboardNavigation: false
  });
  
  const [confirmationDialog, setConfirmationDialog] = useState<ConfirmationDialogState>({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => {},
    onCancel: () => {}
  });

  const handleOptionActivate = (index: number) => {
    const option = MENU_OPTIONS[index];
    if (!option) return;

    setMenuState(prev => ({
      ...prev,
      selectedOption: option.id,
      isKeyboardNavigation: true
    }));

    if (option.id === 'exit') {
      setConfirmationDialog({
        isOpen: true,
        title: 'Exit Application',
        message: 'Are you sure you want to exit the Investment Portfolio Manager?',
        onConfirm: () => {
          window.close();
        },
        onCancel: () => {
          setConfirmationDialog(prev => ({ ...prev, isOpen: false }));
        }
      });
    } else if (option.route) {
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
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <header className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4" style={{ color: '#06402B' }}>
            Investment Portfolio Manager
          </h1>
          <p className="text-lg text-gray-600">
            Main Menu - Use arrow keys to navigate, Enter to select, or keyboard shortcuts
          </p>
        </header>
        
        <main 
          ref={containerRef}
          className="max-w-2xl mx-auto"
          role="menu"
          aria-label="Main navigation menu"
        >
          <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-3">
            {MENU_OPTIONS.map((option, index) => (
              <MenuOption
                key={option.id}
                option={option}
                index={index}
                isSelected={menuState.selectedOption === option.id}
                isKeyboardSelected={isKeyboardNavigation && selectedIndex === index}
                onSelect={handleOptionSelect}
                onKeyPress={handleOptionKeyPress}
              />
            ))}
          </div>
          
          <div className="mt-8 text-center">
            <p className="text-sm text-gray-500">
              Navigation: Use <kbd className="px-2 py-1 bg-gray-200 rounded text-xs">↑↓</kbd> arrow keys or 
              shortcuts <kbd className="px-2 py-1 bg-gray-200 rounded text-xs">1</kbd>, 
              <kbd className="px-2 py-1 bg-gray-200 rounded text-xs">2</kbd>, 
              <kbd className="px-2 py-1 bg-gray-200 rounded text-xs">3</kbd>. 
              Press <kbd className="px-2 py-1 bg-gray-200 rounded text-xs">Enter</kbd> to select, 
              <kbd className="px-2 py-1 bg-gray-200 rounded text-xs">Esc</kbd> to reset.
            </p>
          </div>
        </main>

      <ConfirmationDialog {...confirmationDialog} />
      </div>
    </div>
  );
}
