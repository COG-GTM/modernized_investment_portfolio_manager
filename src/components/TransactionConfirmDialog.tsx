import { useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { CardContent, CardHeader, CardTitle } from './ui/card';
import { trapFocus } from '../utils/accessibility';
import { cn } from '../lib/utils';
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
      <div
        ref={dialogRef}
        className={cn(
          "bg-card text-card-foreground flex flex-col gap-6 rounded-xl border py-6 shadow-sm",
          "w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto"
        )}
      >
        <CardHeader>
          <CardTitle id="confirm-dialog-title" className="text-lg font-semibold">
            Confirm Transaction Submission
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p id="confirm-dialog-description" className="text-sm text-muted-foreground">
            Please review the transaction details below before submitting.
          </p>

          <div className="space-y-3 text-sm">
            <DetailRow label="Transaction ID" value={transaction.transactionId} />
            <DetailRow
              label="Type"
              value={TRANSACTION_TYPE_LABELS[transaction.transactionType]}
            />
            <DetailRow label="Date" value={transaction.transactionDate} />
            {!isTransfer && (
              <DetailRow label="Account Number" value={transaction.accountNumber} />
            )}
            {isTransfer && (
              <>
                <DetailRow label="Source Account" value={transaction.sourceAccount ?? ''} />
                <DetailRow label="Destination Account" value={transaction.destinationAccount ?? ''} />
              </>
            )}
            <DetailRow label="Portfolio ID" value={transaction.portfolioId} />
            {!isFee && <DetailRow label="Fund ID" value={transaction.fundId} />}
            {!isFee && (
              <DetailRow label="Quantity" value={transaction.quantity.toFixed(4)} />
            )}
            {!isFee && !isTransfer && (
              <DetailRow label="Price" value={`$${transaction.price.toFixed(4)}`} />
            )}
            <div className="flex justify-between items-center py-2 px-3 rounded-md bg-primary/5 border border-primary/20">
              <span className="font-medium text-foreground">Amount</span>
              <span className="font-bold text-lg text-primary">
                ${transaction.amount.toFixed(2)}
              </span>
            </div>
            <DetailRow label="Currency" value={transaction.currency} />
            {isFee && transaction.description && (
              <DetailRow label="Description" value={transaction.description} />
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
      </div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center py-1 border-b border-border/50">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium text-foreground">{value}</span>
    </div>
  );
}
