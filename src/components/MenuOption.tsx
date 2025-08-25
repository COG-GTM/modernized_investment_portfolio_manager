import React from 'react';
import { Link } from 'react-router-dom';
import { MenuOption as MenuOptionType } from '../types/menu';

interface MenuOptionProps {
  option: MenuOptionType;
  isSelected: boolean;
  isKeyboardSelected?: boolean;
  index: number;
  onSelect: (optionId: string) => void;
  onKeyPress: (optionId: string) => void;
}

export default function MenuOption({ 
  option, 
  isSelected, 
  isKeyboardSelected = false,
  index,
  onSelect, 
  onKeyPress 
}: MenuOptionProps) {
  const handleClick = () => {
    if (option.action) {
      option.action();
    } else {
      onSelect(option.id);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onKeyPress(option.id);
    }
  };

  const baseClasses = `
    block w-full p-6 rounded-lg border-2 transition-smooth cursor-pointer
    focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary
    transform-gpu will-change-transform
    ${isSelected || isKeyboardSelected
      ? 'border-primary bg-primary/5 shadow-xl scale-105 ring-2 ring-primary/20' 
      : 'border-border bg-card hover:border-primary/50 hover:bg-primary/5 hover:shadow-lg hover:scale-102 hover:-translate-y-1'
    }
    ${isKeyboardSelected ? 'ring-2 ring-primary ring-offset-2' : ''}
  `;

  const content = (
    <div className={`group ${baseClasses}`}
         onClick={handleClick}
         onKeyDown={handleKeyDown}
         tabIndex={0}
         role="button"
         aria-label={`${option.label} - Press ${option.shortcut} or Enter to activate`}
         aria-pressed={isSelected}
         aria-describedby={`option-${index}-description`}
         aria-current={isKeyboardSelected ? 'true' : 'false'}>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xl font-semibold text-foreground">
          {option.label}
        </h2>
        <span className="inline-flex items-center justify-center w-8 h-8 text-sm font-bold text-primary-foreground bg-primary rounded-full shadow-sm transition-smooth group-hover:scale-110">
          {option.shortcut}
        </span>
      </div>
      <p id={`option-${index}-description`} className="text-muted-foreground text-sm leading-relaxed">
        {option.description}
      </p>
    </div>
  );

  if (option.route) {
    return (
      <Link to={option.route} className="block">
        {content}
      </Link>
    );
  }

  return content;
}
