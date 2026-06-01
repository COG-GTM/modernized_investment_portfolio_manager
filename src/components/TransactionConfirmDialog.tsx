import { useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { trapFocus } from '../utils/accessibility';
import type { Transaction } from '../types/transaction';
import { TRANSACTION_TYPE_LABELS } from '../types/transaction';

interface TransactionConfirmDialogProps {
  isOpen: boolean;
  transaction: Omit<Transaction, 'status'> | null;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function TransactionConfirmDialog({
  isOpen,
  transaction,
  onConfirm,
  onCancel,
}: TransactionConfirmDialogProps) {
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

  if (!isOpen || !transaction) return null;

  const isTransfer = transaction.transactionType === 'TR';
  const isFee = transaction.transactionType === 'FE';

  const fields: Array<{ label: string; value: string }> = [
    { label: 'Transaction ID', value: transaction.transactionId },
    { label: 'Type', value: TRANSACTION_TYPE_LABELS[transaction.transactionType] },
    { label: 'Date', value: transaction.transactionDate },
    { label: 'Currency', value: transaction.currency },
  ];

  if (isTransfer) {
    fields.push(
      { label: 'Source Account', value: transaction.sourceAccount || '' },
      { label: 'Destination Account', value: transaction.destinationAccount || '' },
    );
  } else {
    fields.push({ label: 'Account Number', value: transaction.accountNumber });
  }

  fields.push({ label: 'Portfolio ID', value: transaction.portfolioId });

  if (!isFee) {
    fields.push(
      { label: 'Fund ID', value: transaction.fundId },
      { label: 'Quantity', value: transaction.quantity.toFixed(4) },
    );
  }

  if (!isTransfer && !isFee) {
    fields.push({ label: 'Price', value: `$${transaction.price.toFixed(4)}` });
  }

  if (isFee) {
    fields.push(
      { label: 'Fund ID', value: transaction.fundId },
      { label: 'Description', value: transaction.description || '' },
    );
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-desc"
    >
      <Card
        ref={dialogRef}
        className="w-full max-w-lg mx-4"
      >
        <CardHeader>
          <CardTitle id="confirm-dialog-title" className="text-lg font-semibold">
            Confirm Transaction Submission
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p id="confirm-dialog-desc" className="text-sm text-muted-foreground">
            Please review the transaction details below before submitting.
          </p>

          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            {fields.map(({ label, value }) => (
              <div key={label} className="contents">
                <span className="text-muted-foreground font-medium">{label}</span>
                <span className="text-foreground">{value}</span>
              </div>
            ))}
          </div>

          <div className="rounded-md bg-primary/5 border border-primary/20 p-4 text-center">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">Total Amount</p>
            <p className="text-2xl font-bold text-primary">
              ${transaction.amount.toFixed(2)}
            </p>
          </div>

          <div className="flex gap-3 justify-end pt-2">
            <Button
              variant="outline"
              onClick={onCancel}
              className="focus:ring-2 focus:ring-offset-2 focus:ring-primary"
            >
              Edit
            </Button>
            <Button
              variant="default"
              onClick={onConfirm}
              className="focus:ring-2 focus:ring-offset-2 focus:ring-primary"
            >
              Confirm &amp; Submit
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
