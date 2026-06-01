import { useState, useEffect } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button, Alert } from '../components';
import { Input } from '../components/ui/input';
import TransactionConfirmDialog from '../components/TransactionConfirmDialog';
import { transactionStore, generateTransactionId } from '../data/mockTransactions';
import type { Transaction, TransactionType } from '../types/transaction';
import {
  TRANSACTION_TYPE_LABELS,
  LEGACY_ERROR_CODES,
  CURRENCY_OPTIONS,
} from '../types/transaction';

const TRANSACTION_TYPES: TransactionType[] = ['BU', 'SL', 'TR', 'FE'];

function getTodayString(): string {
  const d = new Date();
  return [
    d.getFullYear(),
    String(d.getMonth() + 1).padStart(2, '0'),
    String(d.getDate()).padStart(2, '0'),
  ].join('-');
}

const transactionFormSchema = z
  .object({
    transactionType: z.enum(['BU', 'SL', 'TR', 'FE'], {
      message: `${LEGACY_ERROR_CODES['E003']} [E003]`,
    }),
    accountNumber: z.string().optional(),
    portfolioId: z
      .string()
      .regex(/^[A-Z0-9]{8}$/, `${LEGACY_ERROR_CODES['VAL-INVALID-ID']} [VAL-INVALID-ID]`),
    fundId: z
      .string()
      .regex(/^[A-Z0-9]{6}$/, `${LEGACY_ERROR_CODES['E002']} [E002]`),
    quantity: z.number().optional(),
    price: z.number().optional(),
    amount: z.number().optional(),
    currency: z.string().min(3).max(3),
    transactionDate: z.string().min(1, 'Date is required'),
    sourceAccount: z.string().optional(),
    destinationAccount: z.string().optional(),
    description: z.string().optional(),
  })
  .superRefine((data, ctx) => {
    const type = data.transactionType;

    // Account number validation for non-transfer types
    if (type !== 'TR') {
      if (!data.accountNumber || !/^\d{9}$/.test(data.accountNumber) || parseInt(data.accountNumber, 10) < 100000000) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `${LEGACY_ERROR_CODES['E001']} [E001]`,
          path: ['accountNumber'],
        });
      }
    }

    // Transfer-specific: source and destination account validation
    if (type === 'TR') {
      if (!data.sourceAccount || !/^\d{9}$/.test(data.sourceAccount) || parseInt(data.sourceAccount, 10) < 100000000) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `${LEGACY_ERROR_CODES['E001']} [E001]`,
          path: ['sourceAccount'],
        });
      }
      if (!data.destinationAccount || !/^\d{9}$/.test(data.destinationAccount) || parseInt(data.destinationAccount, 10) < 100000000) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `${LEGACY_ERROR_CODES['E001']} [E001]`,
          path: ['destinationAccount'],
        });
      }
    }

    // Buy/Sell: quantity and price must be > 0
    if (type === 'BU' || type === 'SL') {
      if (data.quantity == null || data.quantity <= 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Quantity must be greater than 0',
          path: ['quantity'],
        });
      }
      if (data.price == null || data.price <= 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Price must be greater than 0',
          path: ['price'],
        });
      }
    }

    // Fee: amount must be non-zero
    if (type === 'FE') {
      if (data.amount == null || data.amount === 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `${LEGACY_ERROR_CODES['VAL-INVALID-AMT']} [VAL-INVALID-AMT]`,
          path: ['amount'],
        });
      }
    }

    // Date must not be in the future
    if (data.transactionDate && data.transactionDate > getTodayString()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Transaction date cannot be in the future',
        path: ['transactionDate'],
      });
    }
  });

type TransactionFormData = z.infer<typeof transactionFormSchema>;

export default function TransactionSubmit() {
  const history = useHistory();
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [pendingTransaction, setPendingTransaction] = useState<Omit<Transaction, 'status'> | null>(null);
  const [zeroDollarWarning, setZeroDollarWarning] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
    trigger,
  } = useForm<TransactionFormData>({
    resolver: zodResolver(transactionFormSchema),
    mode: 'onBlur',
    defaultValues: {
      transactionType: 'BU',
      accountNumber: '',
      portfolioId: '',
      fundId: '',
      quantity: undefined,
      price: undefined,
      amount: undefined,
      currency: 'USD',
      transactionDate: getTodayString(),
      sourceAccount: '',
      destinationAccount: '',
      description: '',
    },
  });

  const transactionType = watch('transactionType');
  const quantity = watch('quantity');
  const price = watch('price');

  const isBuySell = transactionType === 'BU' || transactionType === 'SL';
  const isTransfer = transactionType === 'TR';
  const isFee = transactionType === 'FE';

  // Auto-calculate amount for BUY/SELL and check W001 zero-dollar warning
  useEffect(() => {
    if (isBuySell) {
      const q = Number.isFinite(quantity) ? quantity! : 0;
      const p = Number.isFinite(price) ? price! : 0;
      const calc = parseFloat((q * p).toFixed(4));
      setValue('amount', calc);
      // W001: warn if both quantity and price are non-zero but amount rounds to 0
      setZeroDollarWarning(q > 0 && p > 0 && calc === 0);
    } else {
      setZeroDollarWarning(false);
    }
  }, [quantity, price, isBuySell, setValue]);

  const onSubmit = (data: TransactionFormData) => {
    const txnId = generateTransactionId();
    const amount = isBuySell
      ? parseFloat(((data.quantity || 0) * (data.price || 0)).toFixed(4))
      : (data.amount || 0);

    const transaction: Omit<Transaction, 'status'> = {
      transactionId: txnId,
      transactionType: data.transactionType,
      accountNumber: isTransfer ? (data.sourceAccount || '') : (data.accountNumber || ''),
      portfolioId: data.portfolioId,
      transactionDate: data.transactionDate,
      fundId: data.fundId,
      quantity: isFee ? 0 : (data.quantity || 0),
      price: (isFee || isTransfer) ? 0 : (data.price || 0),
      amount,
      currency: data.currency,
      ...(isTransfer && {
        sourceAccount: data.sourceAccount,
        destinationAccount: data.destinationAccount,
      }),
      ...(isFee && {
        description: data.description,
      }),
    };

    setPendingTransaction(transaction);
    setShowConfirmDialog(true);
  };

  const handleConfirm = () => {
    if (!pendingTransaction) return;

    const { transactionId, ...rest } = pendingTransaction;
    transactionStore.add(rest, transactionId);
    setShowConfirmDialog(false);
    setPendingTransaction(null);
    history.push(`${ROUTES.TRANSACTION_STATUS}?highlight=${transactionId}`);
  };

  const handleCancelConfirm = () => {
    setShowConfirmDialog(false);
  };

  const fieldError = (field: keyof TransactionFormData) => {
    const err = errors[field];
    if (!err) return null;
    return (
      <p className="text-sm text-destructive mt-1">{err.message as string}</p>
    );
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="md">
        <div className="space-y-8">
          <div className="flex items-center justify-between">
            <Link to={ROUTES.MAIN_MENU}>
              <Button variant="secondary" size="sm">
                &larr; Back to Main Menu
              </Button>
            </Link>
          </div>
          <PageHeader
            title="Submit Transaction"
            subtitle="Enter transaction details for processing"
          />

          <main className="space-y-6 animate-slide-up">
            {zeroDollarWarning && (
              <Alert className="bg-yellow-50 border-yellow-300 text-yellow-800 animate-fade-in">
                <strong>Warning [W001]:</strong> {LEGACY_ERROR_CODES['W001']}. You may still submit this transaction.
              </Alert>
            )}

            <Card hover={false} className="animate-fade-in">
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                {/* Transaction Type */}
                <div>
                  <label htmlFor="transactionType" className="block text-sm font-medium text-foreground mb-1">
                    Transaction Type
                  </label>
                  <select
                    id="transactionType"
                    {...register('transactionType')}
                    onBlur={() => trigger('transactionType')}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] outline-none"
                  >
                    {TRANSACTION_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {TRANSACTION_TYPE_LABELS[t]} ({t})
                      </option>
                    ))}
                  </select>
                  {fieldError('transactionType')}
                </div>

                {/* Account Number — shown for BU, SL, FE */}
                {!isTransfer && (
                  <div>
                    <label htmlFor="accountNumber" className="block text-sm font-medium text-foreground mb-1">
                      Account Number
                    </label>
                    <Input
                      id="accountNumber"
                      placeholder="123456789"
                      maxLength={9}
                      {...register('accountNumber')}
                      onBlur={() => trigger('accountNumber')}
                    />
                    {fieldError('accountNumber')}
                  </div>
                )}

                {/* Source / Destination for TRANSFER */}
                {isTransfer && (
                  <>
                    <div>
                      <label htmlFor="sourceAccount" className="block text-sm font-medium text-foreground mb-1">
                        Source Account
                      </label>
                      <Input
                        id="sourceAccount"
                        placeholder="123456789"
                        maxLength={9}
                        {...register('sourceAccount')}
                        onBlur={() => trigger('sourceAccount')}
                      />
                      {fieldError('sourceAccount')}
                    </div>
                    <div>
                      <label htmlFor="destinationAccount" className="block text-sm font-medium text-foreground mb-1">
                        Destination Account
                      </label>
                      <Input
                        id="destinationAccount"
                        placeholder="123456789"
                        maxLength={9}
                        {...register('destinationAccount')}
                        onBlur={() => trigger('destinationAccount')}
                      />
                      {fieldError('destinationAccount')}
                    </div>
                  </>
                )}

                {/* Portfolio ID */}
                <div>
                  <label htmlFor="portfolioId" className="block text-sm font-medium text-foreground mb-1">
                    Portfolio ID
                  </label>
                  <Input
                    id="portfolioId"
                    placeholder="PORT0001"
                    maxLength={8}
                    {...register('portfolioId')}
                    onBlur={() => trigger('portfolioId')}
                  />
                  {fieldError('portfolioId')}
                </div>

                {/* Fund ID */}
                <div>
                  <label htmlFor="fundId" className="block text-sm font-medium text-foreground mb-1">
                    Fund ID
                  </label>
                  <Input
                    id="fundId"
                    placeholder="AAPL01"
                    maxLength={6}
                    {...register('fundId')}
                    onBlur={() => trigger('fundId')}
                  />
                  {fieldError('fundId')}
                </div>

                {/* Quantity — for BU, SL, TR */}
                {!isFee && (
                  <div>
                    <label htmlFor="quantity" className="block text-sm font-medium text-foreground mb-1">
                      Quantity
                    </label>
                    <Input
                      id="quantity"
                      type="number"
                      step="0.0001"
                      min="0"
                      placeholder="0.0000"
                      {...register('quantity', { setValueAs: (v: string) => v === '' ? undefined : Number(v) })}
                      onBlur={() => trigger('quantity')}
                    />
                    {fieldError('quantity')}
                  </div>
                )}

                {/* Price — for BU, SL only */}
                {isBuySell && (
                  <div>
                    <label htmlFor="price" className="block text-sm font-medium text-foreground mb-1">
                      Price
                    </label>
                    <Input
                      id="price"
                      type="number"
                      step="0.0001"
                      min="0"
                      placeholder="0.0000"
                      {...register('price', { setValueAs: (v: string) => v === '' ? undefined : Number(v) })}
                      onBlur={() => trigger('price')}
                    />
                    {fieldError('price')}
                  </div>
                )}

                {/* Amount — auto-calc for BU/SL (read-only), editable for FE */}
                {(isBuySell || isFee) && (
                  <div>
                    <label htmlFor="amount" className="block text-sm font-medium text-foreground mb-1">
                      Amount {isBuySell && <span className="text-muted-foreground text-xs">(auto-calculated)</span>}
                    </label>
                    <Input
                      id="amount"
                      type="number"
                      step="0.01"
                      readOnly={isBuySell}
                      className={isBuySell ? 'bg-muted cursor-not-allowed' : ''}
                      placeholder="0.00"
                      {...register('amount', { setValueAs: (v: string) => v === '' ? undefined : Number(v) })}
                      onBlur={() => trigger('amount')}
                    />
                    {fieldError('amount')}
                  </div>
                )}

                {/* Currency */}
                <div>
                  <label htmlFor="currency" className="block text-sm font-medium text-foreground mb-1">
                    Currency
                  </label>
                  <select
                    id="currency"
                    {...register('currency')}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] outline-none"
                  >
                    {CURRENCY_OPTIONS.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                  {fieldError('currency')}
                </div>

                {/* Transaction Date */}
                <div>
                  <label htmlFor="transactionDate" className="block text-sm font-medium text-foreground mb-1">
                    Transaction Date
                  </label>
                  <Input
                    id="transactionDate"
                    type="date"
                    max={getTodayString()}
                    {...register('transactionDate')}
                    onBlur={() => trigger('transactionDate')}
                  />
                  {fieldError('transactionDate')}
                </div>

                {/* Description — FE only */}
                {isFee && (
                  <div>
                    <label htmlFor="description" className="block text-sm font-medium text-foreground mb-1">
                      Description
                    </label>
                    <Input
                      id="description"
                      placeholder="Fee description"
                      {...register('description')}
                    />
                    {fieldError('description')}
                  </div>
                )}

                <Button type="submit" className="w-full">
                  Review &amp; Submit
                </Button>
              </form>
            </Card>

            <div className="flex justify-center animate-fade-in" style={{ animationDelay: '200ms' }}>
              <Link to={ROUTES.TRANSACTION_STATUS}>
                <Button variant="outline">
                  View Transaction Status
                </Button>
              </Link>
            </div>
          </main>
        </div>
      </Container>

      <TransactionConfirmDialog
        isOpen={showConfirmDialog}
        transaction={pendingTransaction}
        onConfirm={handleConfirm}
        onCancel={handleCancelConfirm}
      />
    </div>
  );
}
