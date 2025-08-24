import { useState, useEffect } from 'react';
import { MENU_OPTIONS, MenuState } from '../types/menu';
import MenuOption from '../components/MenuOption';

export default function MainMenu() {
  const [menuState, setMenuState] = useState<MenuState>({
    selectedOption: null,
    isKeyboardNavigation: false
  });

  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      const key = event.key;
      const option = MENU_OPTIONS.find(opt => opt.shortcut === key);
      
      if (option) {
        event.preventDefault();
        setMenuState(prev => ({
          ...prev,
          selectedOption: option.id,
          isKeyboardNavigation: true
        }));
        
        setTimeout(() => {
          if (option.action) {
            option.action();
          } else if (option.route) {
            window.location.href = option.route;
          }
        }, 150);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  const handleOptionSelect = (optionId: string) => {
    setMenuState(prev => ({
      ...prev,
      selectedOption: optionId,
      isKeyboardNavigation: false
    }));
  };

  const handleOptionKeyPress = (optionId: string) => {
    const option = MENU_OPTIONS.find(opt => opt.id === optionId);
    if (option?.action) {
      option.action();
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
            Main Menu - Select an option below or use keyboard shortcuts
          </p>
        </header>
        
        <main className="max-w-2xl mx-auto">
          <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-3">
            {MENU_OPTIONS.map((option) => (
              <MenuOption
                key={option.id}
                option={option}
                isSelected={menuState.selectedOption === option.id}
                onSelect={handleOptionSelect}
                onKeyPress={handleOptionKeyPress}
              />
            ))}
          </div>
          
          <div className="mt-8 text-center">
            <p className="text-sm text-gray-500">
              Use keyboard shortcuts: Press <kbd className="px-2 py-1 bg-gray-200 rounded text-xs">1</kbd>, <kbd className="px-2 py-1 bg-gray-200 rounded text-xs">2</kbd>, or <kbd className="px-2 py-1 bg-gray-200 rounded text-xs">3</kbd>
            </p>
          </div>
        </main>
      </div>
    </div>
  );
}
