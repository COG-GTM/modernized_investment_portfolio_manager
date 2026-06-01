import { useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { trapFocus } from '../utils/accessibility';
import {
  Transaction,
  TRANSACTION_TYPE_LABELS,
} from '../types/transaction';

interface TransactionConfirmDialogProps {
  isOpen: boolean;
  transaction: Transaction | null;
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

  const isBuySell = transaction.transactionType === 'BU' || transaction.transactionType === 'SL';
  const isTransfer = transaction.transactionType === 'TR';
  const isFee = transaction.transactionType === 'FE';

  const rows: Array<{ label: string; value: string }> = [
    { label: 'Transaction ID', value: transaction.transactionId },
    { label: 'Type', value: TRANSACTION_TYPE_LABELS[transaction.transactionType] },
    { label: 'Date', value: transaction.transactionDate },
  ];

  if (isTransfer) {
    rows.push({ label: 'Source Account', value: transaction.sourceAccount || '' });
    rows.push({ label: 'Destination Account', value: transaction.destinationAccount || '' });
  } else {
    rows.push({ label: 'Account Number', value: transaction.accountNumber });
  }

  rows.push({ label: 'Portfolio ID', value: transaction.portfolioId });

  if (!isFee) {
    rows.push({ label: 'Fund ID', value: transaction.fundId });
  }

  if (isBuySell) {
    rows.push({ label: 'Quantity', value: transaction.quantity.toFixed(4) });
    rows.push({ label: 'Price', value: `$${transaction.price.toFixed(4)}` });
  }

  if (isTransfer) {
    rows.push({ label: 'Quantity', value: transaction.quantity.toFixed(4) });
  }

  rows.push({ label: 'Currency', value: transaction.currency });

  if (isFee && transaction.description) {
    rows.push({ label: 'Description', value: transaction.description });
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-desc"
    >
      <div ref={dialogRef} style={{ width: '100%', maxWidth: '32rem', margin: '0 1rem', maxHeight: '90vh', overflowY: 'auto' }} tabIndex={-1}>
        <Card>
          <CardHeader>
            <CardTitle id="confirm-dialog-title" className="text-lg font-semibold">
              Confirm Transaction Submission
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p id="confirm-dialog-desc" className="text-sm text-muted-foreground">
              Please review the transaction details below before submitting.
            </p>

            <div className="space-y-2">
              {rows.map((row) => (
                <div key={row.label} className="flex justify-between py-1 border-b border-border last:border-0">
                  <span className="text-sm text-muted-foreground">{row.label}</span>
                  <span className="text-sm font-medium">{row.value}</span>
                </div>
              ))}
            </div>

            {/* Amount displayed prominently */}
            <div className="rounded-lg bg-muted/50 p-4 text-center">
              <p className="text-sm text-muted-foreground mb-1">
                {isBuySell ? 'Calculated Amount' : 'Amount'}
              </p>
              <p className="text-2xl font-bold">
                ${transaction.amount.toFixed(2)}
              </p>
              {isBuySell && (
                <p className="text-xs text-muted-foreground mt-1">
                  {transaction.quantity.toFixed(4)} x ${transaction.price.toFixed(4)}
                </p>
              )}
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
    </div>
  );
}
