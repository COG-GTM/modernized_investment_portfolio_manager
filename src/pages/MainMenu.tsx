import { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { MENU_OPTIONS, MenuState } from '../types/menu';
import { useKeyboardNavigation } from '../hooks/useKeyboardNavigation';
import MenuOption from '../components/MenuOption';
import { Container, PageHeader, Card, Button, Alert } from '../components';

const optionSchema = z.object({
  option: z.string()
    .length(1, 'Please enter a single digit')
    .regex(/^[1-3]$/, 'Please enter 1, 2, or 3')
});

type OptionFormData = z.infer<typeof optionSchema>;

export default function MainMenu() {
  const history = useHistory();
  const [menuState, setMenuState] = useState<MenuState>({
    selectedOption: null,
    isKeyboardNavigation: false
  });
  const [error, setError] = useState<string | null>(null);
  
  const { register, handleSubmit, formState: { errors }, reset } = useForm<OptionFormData>({
    resolver: zodResolver(optionSchema),
    mode: 'onSubmit',
  });

  const handleExitConfirmation = () => {
    const confirmed = window.confirm(
      'Are you sure you want to exit the Portfolio Management System?'
    );
    if (confirmed) {
      setError(null);
      alert('Thank you for using the Portfolio Management System.');
      reset();
    }
  };

  const navigateToOption = (optionNumber: string) => {
    const index = parseInt(optionNumber) - 1;
    const option = MENU_OPTIONS[index];
    
    if (!option) {
      setError('Invalid option selected. Please enter 1, 2, or 3.');
      return;
    }

    setMenuState(prev => ({
      ...prev,
      selectedOption: option.id,
      isKeyboardNavigation: false
    }));

    setError(null);

    if (option.id === 'exit') {
      handleExitConfirmation();
    } else if (option.route) {
      setTimeout(() => history.push(option.route!), 150);
    } else if (option.action) {
      option.action();
    }
  };

  const onSubmit = (data: OptionFormData) => {
    navigateToOption(data.option);
  };

  const handleOptionActivate = (index: number) => {
    const option = MENU_OPTIONS[index];
    if (!option) return;

    setMenuState(prev => ({
      ...prev,
      selectedOption: option.id,
      isKeyboardNavigation: true
    }));

    setError(null);

    if (option.id === 'exit') {
      handleExitConfirmation();
    } else if (option.route) {
      setTimeout(() => history.push(option.route!), 150);
    } else if (option.action) {
      option.action();
    }
  };

  const handleNumberKeyActivate = (key: string) => {
    navigateToOption(key);
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
            title="Portfolio Management System"
            subtitle="View, analyze, and manage investment portfolios"
            className="mb-12"
          />
          
          <Card className="max-w-md mx-auto animate-fade-in">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <label htmlFor="option" className="block text-sm font-medium mb-2">
                  Select Option:
                </label>
                <input
                  id="option"
                  type="text"
                  maxLength={1}
                  {...register('option')}
                  className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder="Enter 1, 2, or 3"
                  aria-label="Option selection"
                  aria-describedby="option-help"
                />
                {errors.option && (
                  <p className="mt-1 text-sm text-red-600" role="alert">
                    {errors.option.message}
                  </p>
                )}
                <p id="option-help" className="mt-1 text-sm text-muted-foreground">
                  Enter the number of your choice and press Enter
                </p>
              </div>
              <Button type="submit" className="w-full">
                Submit
              </Button>
            </form>
          </Card>
          
          <main 
            ref={containerRef}
            className="mx-auto"
            role="menu"
            aria-label="Main navigation menu"
          >
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 max-w-6xl mx-auto animate-slide-up">
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
                <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono shadow-sm">2</kbd>,
                <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono shadow-sm">3</kbd>. 
                Press <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono shadow-sm">Enter</kbd> to select, 
                <kbd className="px-2 py-1 bg-muted rounded text-xs font-mono shadow-sm">Esc</kbd> to reset.
              </p>
            </div>
          </main>

          {error && (
            <div className="max-w-4xl mx-auto animate-fade-in">
              <Alert variant="destructive">
                {error}
              </Alert>
            </div>
          )}
        </div>
      </Container>
    </div>
  );
}
