import { useState, FormEvent, ChangeEvent, KeyboardEvent } from 'react';
import { useHistory } from 'react-router-dom';
import { ROUTES } from '../types/routes';

export default function Menu() {
  const history = useHistory();
  const [option, setOption] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrorMessage('');

    const trimmedOption = option.trim();

    if (!trimmedOption) {
      setErrorMessage('Please enter an option (1-3)');
      return;
    }

    if (!/^\d$/.test(trimmedOption)) {
      setErrorMessage('Invalid input. Please enter a single digit (1-3)');
      return;
    }

    const optionNum = parseInt(trimmedOption, 10);

    if (optionNum < 1 || optionNum > 3) {
      setErrorMessage('Invalid option. Please enter 1, 2, or 3');
      return;
    }

    switch (optionNum) {
      case 1:
        history.push(ROUTES.PORTFOLIO_INQUIRY);
        break;
      case 2:
        history.push(ROUTES.TRANSACTION_HISTORY);
        break;
      case 3:
        handleExit();
        break;
      default:
        setErrorMessage('Invalid option. Please enter 1, 2, or 3');
    }
  };

  const handleExit = () => {
    if (window.confirm('Are you sure you want to exit?')) {
      window.location.href = '/';
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value === '' || /^\d$/.test(value)) {
      setOption(value);
      setErrorMessage('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center py-8">
      <div className="w-full max-w-2xl px-4">
        <div className="bg-card border border-border rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-foreground mb-8 text-center">
            Portfolio Management System
          </h1>

          <div className="space-y-4 mb-8">
            <p className="text-lg font-semibold text-foreground">
              Select Option:
            </p>
            
            <div className="space-y-2 ml-4">
              <p className="text-base text-foreground">
                1. Portfolio Position Inquiry
              </p>
              <p className="text-base text-foreground">
                2. Transaction History
              </p>
              <p className="text-base text-foreground">
                3. Exit
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="flex items-center gap-4">
              <label htmlFor="option-input" className="text-base font-medium text-foreground">
                Option:
              </label>
              <input
                id="option-input"
                type="text"
                value={option}
                onChange={handleInputChange}
                onKeyPress={handleKeyPress}
                maxLength={1}
                className="w-16 px-3 py-2 border border-input rounded-md text-center text-lg font-mono bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent"
                placeholder=""
                autoFocus
              />
            </div>

            <button
              type="submit"
              className="w-full px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 font-medium transition-colors"
            >
              Submit
            </button>
          </form>

          {errorMessage && (
            <div className="mt-6 p-4 bg-destructive/10 border border-destructive rounded-md">
              <p className="text-destructive text-sm font-medium" style={{ maxWidth: '78ch' }}>
                {errorMessage}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
