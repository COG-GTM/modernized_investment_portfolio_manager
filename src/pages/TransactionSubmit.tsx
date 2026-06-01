import { useState, useCallback } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button, Alert } from '../components';
import { Input } from '../components/ui/input';
import TransactionConfirmDialog from '../components/TransactionConfirmDialog';
import { transactionStore } from '../data/mockTransactions';
import {
  TransactionType,
  Transaction,
  TRANSACTION_TYPE_LABELS,
  LEGACY_ERROR_CODES,
} from '../types/transaction';

const VALID_TYPES: TransactionType[] = ['BU', 'SL', 'TR', 'FE'];

function safeNum(v: number | undefined | null): number {
  if (v === undefined || v === null || Number.isNaN(v)) return 0;
  return v;
}

function getTodayString(): string {
  const now = new Date();
  return (
    now.getFullYear() +
    '-' +
    String(now.getMonth() + 1).padStart(2, '0') +
    '-' +
    String(now.getDate()).padStart(2, '0')
  );
}

const transactionSchema = z
  .object({
    transactionType: z.enum(['BU', 'SL', 'TR', 'FE'] as const, {
      error: `[E003] ${LEGACY_ERROR_CODES['E003']}`,
    }),
    accountNumber: z.string().optional(),
    portfolioId: z
      .string()
      .regex(/^[A-Z0-9]{8}$/, `[VAL-INVALID-ID] ${LEGACY_ERROR_CODES['VAL-INVALID-ID']}`),
    fundId: z.string().optional(),
    quantity: z.number().optional(),
    price: z.number().optional(),
    amount: z.number().optional(),
    currency: z
      .string()
      .regex(/^[A-Z]{3}$/, 'Currency must be a 3-letter ISO code'),
    transactionDate: z.string().min(1, 'Date is required'),
    sourceAccount: z.string().optional(),
    destinationAccount: z.string().optional(),
    description: z.string().optional(),
  })
  .superRefine((data, ctx) => {
    const type = data.transactionType;
    const isBuySell = type === 'BU' || type === 'SL';
    const isTransfer = type === 'TR';
    const isFee = type === 'FE';

    // Account number validation for non-transfer types
    if (!isTransfer) {
      if (
        !data.accountNumber ||
        !/^\d{9}$/.test(data.accountNumber) ||
        parseInt(data.accountNumber, 10) < 100000000
      ) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['accountNumber'],
          message: `[E001] ${LEGACY_ERROR_CODES['E001']}`,
        });
      }
    }

    // Fund ID validation for non-fee types
    if (!isFee) {
      if (!data.fundId || !/^[A-Z0-9]{6}$/.test(data.fundId)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['fundId'],
          message: `[E002] ${LEGACY_ERROR_CODES['E002']}`,
        });
      }
    }

    // Quantity >= 0 for BUY/SELL (zero allowed — triggers W001 warning)
    if (isBuySell && (data.quantity === undefined || data.quantity < 0)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['quantity'],
        message: 'Quantity must be zero or greater for Buy/Sell transactions',
      });
    }

    // Price >= 0 for BUY/SELL (zero allowed — triggers W001 warning)
    if (isBuySell && (data.price === undefined || data.price < 0)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['price'],
        message: 'Price must be zero or greater for Buy/Sell transactions',
      });
    }

    // Amount != 0 for FEE
    if (isFee && (data.amount === undefined || data.amount === 0)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['amount'],
        message: `[VAL-INVALID-AMT] ${LEGACY_ERROR_CODES['VAL-INVALID-AMT']}`,
      });
    }

    // Transfer: source and destination required
    if (isTransfer) {
      if (
        !data.sourceAccount ||
        !/^\d{9}$/.test(data.sourceAccount) ||
        parseInt(data.sourceAccount, 10) < 100000000
      ) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['sourceAccount'],
          message: `[E001] ${LEGACY_ERROR_CODES['E001']}`,
        });
      }
      if (
        !data.destinationAccount ||
        !/^\d{9}$/.test(data.destinationAccount) ||
        parseInt(data.destinationAccount, 10) < 100000000
      ) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ['destinationAccount'],
          message: `[E001] ${LEGACY_ERROR_CODES['E001']}`,
        });
      }
    }

    // Quantity for transfers
    if (isTransfer && (data.quantity === undefined || data.quantity <= 0)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['quantity'],
        message: 'Quantity must be greater than 0 for Transfer transactions',
      });
    }

    // Date <= today
    if (data.transactionDate && data.transactionDate > getTodayString()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['transactionDate'],
        message: 'Transaction date cannot be in the future',
      });
    }
  });

type TransactionFormData = z.infer<typeof transactionSchema>;

function generatePreviewTransactionId(): string {
  const now = new Date();
  const dateStr =
    now.getFullYear().toString() +
    String(now.getMonth() + 1).padStart(2, '0') +
    String(now.getDate()).padStart(2, '0');
  return `${dateStr}-${String(Math.floor(Math.random() * 9000) + 1000).padStart(4, '0')}`;
}

export default function TransactionSubmit() {
  const history = useHistory();
  const [showConfirm, setShowConfirm] = useState(false);
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
    resolver: zodResolver(transactionSchema),
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

  const transactionType = watch('transactionType') as TransactionType;
  const quantity = watch('quantity');
  const price = watch('price');

  const isBuySell = transactionType === 'BU' || transactionType === 'SL';
  const isTransfer = transactionType === 'TR';
  const isFee = transactionType === 'FE';

  // Auto-calculate amount for BUY/SELL
  const calculatedAmount = isBuySell
    ? safeNum(quantity) * safeNum(price)
    : undefined;

  const handleAutoCalcBlur = useCallback(() => {
    if (isBuySell) {
      const amt = safeNum(quantity) * safeNum(price);
      setValue('amount', amt);
      setZeroDollarWarning(amt === 0);
    }
  }, [isBuySell, quantity, price, setValue]);

  const onFormSubmit = (data: TransactionFormData) => {
    const amount = isBuySell
      ? safeNum(data.quantity) * safeNum(data.price)
      : isFee ? safeNum(data.amount) : 0;

    // Update zero-dollar warning state on submit
    setZeroDollarWarning(isBuySell && amount === 0);

    const preview: Omit<Transaction, 'status'> = {
      transactionId: generatePreviewTransactionId(),
      transactionType: data.transactionType as TransactionType,
      accountNumber: isTransfer ? (data.sourceAccount ?? '') : (data.accountNumber ?? ''),
      portfolioId: data.portfolioId,
      transactionDate: data.transactionDate,
      fundId: isFee ? 'FEE001' : (data.fundId ?? ''),
      quantity: safeNum(data.quantity),
      price: isBuySell ? safeNum(data.price) : 0,
      amount,
      currency: data.currency,
      ...(isTransfer && {
        sourceAccount: data.sourceAccount,
        destinationAccount: data.destinationAccount,
      }),
      ...(isFee && { description: data.description }),
    };

    setPendingTransaction(preview);
    setShowConfirm(true);
  };

  const handleConfirm = () => {
    if (!pendingTransaction) return;

    const { transactionId: _id, ...rest } = pendingTransaction;
    const created = transactionStore.add(rest);
    setShowConfirm(false);
    setPendingTransaction(null);
    history.push(`${ROUTES.TRANSACTION_STATUS}?highlight=${created.transactionId}`);
  };

  const handleCancelConfirm = () => {
    setShowConfirm(false);
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <Container size="md">
        <div className="space-y-8">
          <div className="flex items-center justify-between">
            <Link to={ROUTES.MAIN_MENU}>
              <Button variant="secondary" size="sm">
                ← Back to Main Menu
              </Button>
            </Link>
          </div>
          <PageHeader
            title="Submit Transaction"
            subtitle="Enter transaction details for processing"
          />

          <main className="space-y-6 animate-slide-up">
            {zeroDollarWarning && (
              <Alert className="animate-fade-in bg-yellow-50 border-yellow-300 text-yellow-800">
                <strong>[W001]</strong> {LEGACY_ERROR_CODES['W001']}
              </Alert>
            )}

            <Card hover className="animate-fade-in">
              <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
                {/* Transaction Type */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Transaction Type
                  </label>
                  <select
                    {...register('transactionType')}
                    onChange={(e) => {
                      register('transactionType').onChange(e);
                      setZeroDollarWarning(false);
                      trigger();
                    }}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                  >
                    {VALID_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {TRANSACTION_TYPE_LABELS[t]}
                      </option>
                    ))}
                  </select>
                  {errors.transactionType && (
                    <p className="mt-1 text-sm text-destructive">{errors.transactionType.message}</p>
                  )}
                </div>

                {/* Account Number (BUY/SELL/FEE) */}
                {!isTransfer && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Account Number
                    </label>
                    <Input
                      {...register('accountNumber')}
                      placeholder="123456789"
                      maxLength={9}
                      aria-invalid={!!errors.accountNumber}
                    />
                    {errors.accountNumber && (
                      <p className="mt-1 text-sm text-destructive">{errors.accountNumber.message}</p>
                    )}
                  </div>
                )}

                {/* Source / Destination Account (TRANSFER) */}
                {isTransfer && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Source Account
                      </label>
                      <Input
                        {...register('sourceAccount')}
                        placeholder="123456789"
                        maxLength={9}
                        aria-invalid={!!errors.sourceAccount}
                      />
                      {errors.sourceAccount && (
                        <p className="mt-1 text-sm text-destructive">{errors.sourceAccount.message}</p>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-1">
                        Destination Account
                      </label>
                      <Input
                        {...register('destinationAccount')}
                        placeholder="987654321"
                        maxLength={9}
                        aria-invalid={!!errors.destinationAccount}
                      />
                      {errors.destinationAccount && (
                        <p className="mt-1 text-sm text-destructive">{errors.destinationAccount.message}</p>
                      )}
                    </div>
                  </>
                )}

                {/* Portfolio ID */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Portfolio ID
                  </label>
                  <Input
                    {...register('portfolioId')}
                    placeholder="PORT0001"
                    maxLength={8}
                    aria-invalid={!!errors.portfolioId}
                  />
                  {errors.portfolioId && (
                    <p className="mt-1 text-sm text-destructive">{errors.portfolioId.message}</p>
                  )}
                </div>

                {/* Fund ID (not for FEE) */}
                {!isFee && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Fund ID
                    </label>
                    <Input
                      {...register('fundId')}
                      placeholder="AAPL01"
                      maxLength={6}
                      aria-invalid={!!errors.fundId}
                    />
                    {errors.fundId && (
                      <p className="mt-1 text-sm text-destructive">{errors.fundId.message}</p>
                    )}
                  </div>
                )}

                {/* Quantity (BUY/SELL/TRANSFER) */}
                {!isFee && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Quantity
                    </label>
                    <Input
                      {...register('quantity', { valueAsNumber: true })}
                      type="number"
                      step="0.0001"
                      min="0"
                      placeholder="0.0000"
                      onBlur={(e) => {
                        register('quantity').onBlur(e);
                        handleAutoCalcBlur();
                      }}
                      aria-invalid={!!errors.quantity}
                    />
                    {errors.quantity && (
                      <p className="mt-1 text-sm text-destructive">{errors.quantity.message}</p>
                    )}
                  </div>
                )}

                {/* Price (BUY/SELL only) */}
                {isBuySell && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Price
                    </label>
                    <Input
                      {...register('price', { valueAsNumber: true })}
                      type="number"
                      step="0.0001"
                      min="0"
                      placeholder="0.0000"
                      onBlur={(e) => {
                        register('price').onBlur(e);
                        handleAutoCalcBlur();
                      }}
                      aria-invalid={!!errors.price}
                    />
                    {errors.price && (
                      <p className="mt-1 text-sm text-destructive">{errors.price.message}</p>
                    )}
                  </div>
                )}

                {/* Amount — auto-calc read-only for BUY/SELL, editable for FEE */}
                {(isBuySell || isFee) && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Amount {isBuySell && '(auto-calculated)'}
                    </label>
                    {isBuySell ? (
                      <Input
                        type="text"
                        readOnly
                        value={
                          calculatedAmount !== undefined
                            ? `$${calculatedAmount.toFixed(2)}`
                            : '$0.00'
                        }
                        className="bg-muted cursor-not-allowed"
                      />
                    ) : (
                      <>
                        <Input
                          {...register('amount', { valueAsNumber: true })}
                          type="number"
                          step="0.01"
                          placeholder="0.00"
                          aria-invalid={!!errors.amount}
                        />
                        {errors.amount && (
                          <p className="mt-1 text-sm text-destructive">{errors.amount.message}</p>
                        )}
                      </>
                    )}
                  </div>
                )}

                {/* Currency */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Currency
                  </label>
                  <Input
                    {...register('currency')}
                    placeholder="USD"
                    maxLength={3}
                    aria-invalid={!!errors.currency}
                  />
                  {errors.currency && (
                    <p className="mt-1 text-sm text-destructive">{errors.currency.message}</p>
                  )}
                </div>

                {/* Transaction Date */}
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">
                    Transaction Date
                  </label>
                  <Input
                    {...register('transactionDate')}
                    type="date"
                    max={getTodayString()}
                    aria-invalid={!!errors.transactionDate}
                  />
                  {errors.transactionDate && (
                    <p className="mt-1 text-sm text-destructive">{errors.transactionDate.message}</p>
                  )}
                </div>

                {/* Description (FEE only) */}
                {isFee && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-1">
                      Description
                    </label>
                    <Input
                      {...register('description')}
                      placeholder="Fee description"
                    />
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
        isOpen={showConfirm}
        transaction={pendingTransaction}
        onConfirm={handleConfirm}
        onCancel={handleCancelConfirm}
      />
    </div>
  );
}
