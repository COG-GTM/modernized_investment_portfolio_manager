import { useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { trapFocus } from '../utils/accessibility';
import {
  TRANSACTION_TYPE_LABELS,
  type TransactionType,
} from '../types/transaction';

interface TransactionSummary {
  transactionId: string;
  transactionType: TransactionType;
  accountNumber: string;
  portfolioId: string;
  transactionDate: string;
  fundId: string;
  quantity: number;
  price: number;
  amount: number;
  currency: string;
  sourceAccount?: string;
  destinationAccount?: string;
  description?: string;
}

interface TransactionConfirmDialogProps {
  isOpen: boolean;
  summary: TransactionSummary | null;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function TransactionConfirmDialog({
  isOpen,
  summary,
  onConfirm,
  onCancel,
}: TransactionConfirmDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      const cleanup = dialogRef.current
        ? trapFocus(dialogRef.current)
        : () => {};
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

  if (!isOpen || !summary) return null;

  const isTransfer = summary.transactionType === 'TR';
  const isFee = summary.transactionType === 'FE';

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: summary.currency,
      minimumFractionDigits: 2,
    }).format(value);

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

          <div className="rounded-md border p-4 space-y-3 text-sm">
            <Row label="Transaction ID" value={summary.transactionId} />
            <Row
              label="Type"
              value={TRANSACTION_TYPE_LABELS[summary.transactionType]}
            />
            <Row label="Date" value={summary.transactionDate} />
            {!isTransfer && (
              <Row label="Account Number" value={summary.accountNumber} />
            )}
            {isTransfer && (
              <>
                <Row
                  label="Source Account"
                  value={summary.sourceAccount ?? ''}
                />
                <Row
                  label="Destination Account"
                  value={summary.destinationAccount ?? ''}
                />
              </>
            )}
            <Row label="Portfolio ID" value={summary.portfolioId} />
            <Row label="Fund ID" value={summary.fundId} />
            {!isFee && (
              <>
                <Row
                  label="Quantity"
                  value={summary.quantity.toFixed(4)}
                />
                <Row label="Price" value={formatCurrency(summary.price)} />
              </>
            )}
            <div className="flex justify-between items-center pt-2 border-t font-semibold">
              <span>Amount</span>
              <span className="text-lg">{formatCurrency(summary.amount)}</span>
            </div>
            <Row label="Currency" value={summary.currency} />
            {isFee && summary.description && (
              <Row label="Description" value={summary.description} />
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
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
