import { useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { trapFocus } from '../utils/accessibility';
import type { Transaction } from '../types/transaction';
import { TRANSACTION_TYPE_LABELS, STATUS_LABELS } from '../types/transaction';

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

  const isTransfer = transaction.transactionType === 'TR';
  const isFee = transaction.transactionType === 'FE';
  const isBuySell = transaction.transactionType === 'BU' || transaction.transactionType === 'SL';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-description"
    >
      <Card ref={dialogRef} className="w-full max-w-lg mx-4">
        <CardHeader>
          <CardTitle id="confirm-dialog-title" className="text-lg font-semibold">
            Confirm Transaction Submission
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p id="confirm-dialog-description" className="text-sm text-muted-foreground">
            Please review the transaction details below before submitting.
          </p>

          <div className="space-y-3 rounded-md border p-4 text-sm">
            <SummaryRow label="Transaction ID" value={transaction.transactionId} highlight />
            <SummaryRow label="Type" value={TRANSACTION_TYPE_LABELS[transaction.transactionType]} />
            <SummaryRow label="Status" value={STATUS_LABELS[transaction.status]} />
            <SummaryRow label="Date" value={transaction.transactionDate} />

            {isTransfer ? (
              <>
                <SummaryRow label="Source Account" value={transaction.sourceAccount ?? ''} />
                <SummaryRow label="Destination Account" value={transaction.destinationAccount ?? ''} />
              </>
            ) : (
              <SummaryRow label="Account Number" value={transaction.accountNumber} />
            )}

            <SummaryRow label="Portfolio ID" value={transaction.portfolioId} />

            {!isFee && <SummaryRow label="Fund ID" value={transaction.fundId} />}

            {isBuySell && (
              <>
                <SummaryRow label="Quantity" value={transaction.quantity.toFixed(4)} />
                <SummaryRow label="Price" value={`$${transaction.price.toFixed(4)}`} />
              </>
            )}

            {isFee && transaction.description && (
              <SummaryRow label="Description" value={transaction.description} />
            )}

            <div className="border-t pt-3 mt-3">
              <SummaryRow
                label="Amount"
                value={`$${transaction.amount.toFixed(2)}`}
                highlight
              />
            </div>

            <SummaryRow label="Currency" value={transaction.currency} />
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

function SummaryRow({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className="flex justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className={highlight ? 'font-semibold text-primary' : 'font-medium'}>{value}</span>
    </div>
  );
}
