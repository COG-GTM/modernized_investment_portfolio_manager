import { useState, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { MENU_OPTIONS, menuFormSchema, type MenuFormData } from '../types/menu';
import { Container, PageHeader, Alert } from '../components';
import { Input } from '../components/ui/input';
import { cn } from '../lib/utils';

export default function MainMenu() {
  const history = useHistory();
  const [error, setError] = useState<string | null>(null);
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    setFocus
  } = useForm<MenuFormData>({
    resolver: zodResolver(menuFormSchema),
    mode: 'onSubmit',
  });

  useEffect(() => {
    setFocus('option');
  }, [setFocus]);

  const onSubmit = (data: MenuFormData) => {
    setError(null);
    const option = MENU_OPTIONS.find(opt => opt.shortcut === data.option);
    
    if (option && option.route) {
      history.push(option.route);
    } else {
      setError('Invalid option selected. Please enter 1, 2, or 3.');
    }
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="md">
        <div className="space-y-8">
          <PageHeader 
            title="Portfolio Management System"
            subtitle=""
            className="mb-8"
          />
          
          <main className="max-w-2xl mx-auto space-y-8">
            <div className="space-y-6">
              <h2 className="text-lg font-medium">Select Option:</h2>
              
              <div className="space-y-2 pl-6">
                {MENU_OPTIONS.map((option) => (
                  <div key={option.id} className="text-base">
                    {option.shortcut}. {option.label}
                  </div>
                ))}
              </div>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <div className="space-y-2 pl-6">
                <label htmlFor="option" className="sr-only">
                  Menu Option
                </label>
                <Input
                  id="option"
                  type="text"
                  maxLength={1}
                  placeholder=""
                  className={cn(
                    'w-16 text-center text-lg font-mono',
                    errors.option && 'border-destructive focus-visible:border-destructive'
                  )}
                  {...register('option')}
                  aria-invalid={errors.option ? 'true' : 'false'}
                  aria-describedby={errors.option ? 'option-error' : undefined}
                />
              </div>

              {(errors.option || error) && (
                <Alert variant="destructive" className="max-w-[78ch]" role="alert">
                  <span id="option-error">
                    {errors.option?.message || error}
                  </span>
                </Alert>
              )}
            </form>

            <div className="text-sm text-muted-foreground pl-6">
              Enter your selection (1-3) and press Enter
            </div>
          </main>
        </div>
      </Container>
    </div>
  );
}
