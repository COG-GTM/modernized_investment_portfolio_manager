import { useEffect, useRef } from 'react';
import { Button } from './ui/button';
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

  const isBuyOrSell = transaction.transactionType === 'BU' || transaction.transactionType === 'SL';
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
        className="bg-card text-card-foreground w-full max-w-lg mx-4 rounded-xl border shadow-lg"
      >
        <div className="px-6 pt-6 pb-2">
          <h2 id="confirm-dialog-title" className="text-lg font-semibold">
            Confirm Transaction Submission
          </h2>
          <p id="confirm-dialog-description" className="text-sm text-muted-foreground mt-1">
            Please review the details below before submitting.
          </p>
        </div>

        <div className="px-6 py-4 space-y-3">
          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <Row label="Transaction ID" value="Assigned on submission" />
            <Row label="Type" value={TRANSACTION_TYPE_LABELS[transaction.transactionType]} />
            <Row label="Date" value={transaction.transactionDate} />
            <Row label="Currency" value={transaction.currency} />

            {(isBuyOrSell || isFee) && (
              <Row label="Account Number" value={transaction.accountNumber} />
            )}
            {isTransfer && (
              <>
                <Row label="Source Account" value={transaction.sourceAccount ?? ''} />
                <Row label="Destination Account" value={transaction.destinationAccount ?? ''} />
              </>
            )}

            <Row label="Portfolio ID" value={transaction.portfolioId} />

            {(isBuyOrSell || isTransfer) && (
              <>
                <Row label="Fund ID" value={transaction.fundId} />
                <Row label="Quantity" value={transaction.quantity.toFixed(4)} />
              </>
            )}

            {(isBuyOrSell || isTransfer) && (
              <Row label="Price" value={`$${transaction.price.toFixed(2)}`} />
            )}

            {isFee && transaction.description && (
              <Row label="Description" value={transaction.description} />
            )}
          </div>

          <div className="border-t pt-3 mt-3">
            <div className="flex items-center justify-between">
              <span className="text-base font-semibold">Total Amount</span>
              <span className="text-xl font-bold text-primary">
                ${transaction.amount.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        <div className="flex gap-3 justify-end px-6 pb-6">
          <Button
            variant="outline"
            onClick={onCancel}
          >
            Edit
          </Button>
          <Button
            variant="default"
            onClick={onConfirm}
          >
            Confirm &amp; Submit
          </Button>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <>
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium text-right">{value}</span>
    </>
  );
}
