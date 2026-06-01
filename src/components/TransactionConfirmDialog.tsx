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

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-description"
    >
      <Card
        ref={dialogRef}
        className="w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto"
      >
        <CardHeader>
          <CardTitle id="confirm-dialog-title" className="text-lg font-semibold">
            Confirm Transaction Submission
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p id="confirm-dialog-description" className="text-sm text-gray-600">
            Please review the transaction details below before submitting.
          </p>

          <div className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-2 border-b pb-2">
              <span className="font-medium text-muted-foreground">Transaction ID</span>
              <span className="font-mono">{transaction.transactionId}</span>
            </div>
            <div className="grid grid-cols-2 gap-2 border-b pb-2">
              <span className="font-medium text-muted-foreground">Type</span>
              <span>{TRANSACTION_TYPE_LABELS[transaction.transactionType]} ({transaction.transactionType})</span>
            </div>
            <div className="grid grid-cols-2 gap-2 border-b pb-2">
              <span className="font-medium text-muted-foreground">Date</span>
              <span>{transaction.transactionDate}</span>
            </div>

            {isTransfer ? (
              <>
                <div className="grid grid-cols-2 gap-2 border-b pb-2">
                  <span className="font-medium text-muted-foreground">Source Account</span>
                  <span className="font-mono">{transaction.sourceAccount}</span>
                </div>
                <div className="grid grid-cols-2 gap-2 border-b pb-2">
                  <span className="font-medium text-muted-foreground">Destination Account</span>
                  <span className="font-mono">{transaction.destinationAccount}</span>
                </div>
              </>
            ) : (
              <div className="grid grid-cols-2 gap-2 border-b pb-2">
                <span className="font-medium text-muted-foreground">Account Number</span>
                <span className="font-mono">{transaction.accountNumber}</span>
              </div>
            )}

            <div className="grid grid-cols-2 gap-2 border-b pb-2">
              <span className="font-medium text-muted-foreground">Portfolio ID</span>
              <span className="font-mono">{transaction.portfolioId}</span>
            </div>

            {!isFee && (
              <div className="grid grid-cols-2 gap-2 border-b pb-2">
                <span className="font-medium text-muted-foreground">Fund ID</span>
                <span className="font-mono">{transaction.fundId}</span>
              </div>
            )}

            {!isFee && (
              <>
                <div className="grid grid-cols-2 gap-2 border-b pb-2">
                  <span className="font-medium text-muted-foreground">Quantity</span>
                  <span>{transaction.quantity.toFixed(4)}</span>
                </div>
                {!isTransfer && (
                  <div className="grid grid-cols-2 gap-2 border-b pb-2">
                    <span className="font-medium text-muted-foreground">Price</span>
                    <span>${transaction.price.toFixed(4)}</span>
                  </div>
                )}
              </>
            )}

            <div className="grid grid-cols-2 gap-2 border-b pb-2">
              <span className="font-medium text-muted-foreground">Currency</span>
              <span>{transaction.currency}</span>
            </div>

            {isFee && transaction.description && (
              <div className="grid grid-cols-2 gap-2 border-b pb-2">
                <span className="font-medium text-muted-foreground">Description</span>
                <span>{transaction.description}</span>
              </div>
            )}

            <div className="grid grid-cols-2 gap-2 bg-muted/50 rounded-md p-3 mt-2">
              <span className="font-semibold">Amount</span>
              <span className="font-semibold text-lg">${transaction.amount.toFixed(2)}</span>
            </div>
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
