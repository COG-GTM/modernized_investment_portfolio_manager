import { useEffect, useRef } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { trapFocus } from '../../utils/accessibility';
import { ConfirmationDialogState } from '../../types/navigation';

interface ConfirmationDialogProps extends ConfirmationDialogState {
  className?: string;
}

export default function ConfirmationDialog({
  isOpen,
  title,
  message,
  onConfirm,
  onCancel,
  className = ''
}: ConfirmationDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      
      const cleanup = dialogRef.current ? trapFocus(dialogRef.current) : () => {};
      
      return cleanup;
    } else if (previousFocusRef.current) {
      previousFocusRef.current.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        e.preventDefault();
        onCancel();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
      aria-describedby="dialog-description"
    >
      <Card
        ref={dialogRef}
        className={`w-full max-w-md mx-4 ${className}`}
      >
        <CardHeader>
          <CardTitle id="dialog-title" className="text-lg font-semibold">
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p id="dialog-description" className="text-gray-600">
            {message}
          </p>
          <div className="flex gap-3 justify-end">
            <Button
              variant="outline"
              onClick={onCancel}
              className="focus:ring-2 focus:ring-offset-2 focus:ring-primary"
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={onConfirm}
              className="focus:ring-2 focus:ring-offset-2 focus:ring-destructive"
            >
              Exit Application
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
