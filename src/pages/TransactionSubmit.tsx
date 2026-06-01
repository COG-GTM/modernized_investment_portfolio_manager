import { useState, useEffect } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button, Alert } from '../components';
import { Input } from '../components/ui/input';
import TransactionConfirmDialog from '../components/TransactionConfirmDialog';
import { transactionStore } from '../data/mockTransactions';
import type { Transaction, TransactionType } from '../types/transaction';
import { TRANSACTION_TYPE_LABELS, LEGACY_ERROR_CODES } from '../types/transaction';

// --- Zod schema with legacy COBOL error code mapping ---

const transactionSchema = z
  .object({
    transactionType: z.enum(['BU', 'SL', 'TR', 'FE'], {
      message: `[E003] ${LEGACY_ERROR_CODES['E003']}`,
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
      .length(3, 'Currency must be a 3-character ISO code')
      .regex(/^[A-Z]{3}$/, 'Currency must be uppercase letters'),
    transactionDate: z.string().min(1, 'Transaction date is required'),
    sourceAccount: z.string().optional(),
    destinationAccount: z.string().optional(),
    description: z.string().optional(),
  })
  .superRefine((data, ctx) => {
    const type = data.transactionType;

    // Account number validation — BU, SL, FE require it
    if (type !== 'TR') {
      if (!data.accountNumber || !/^\d{9}$/.test(data.accountNumber)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `[E001] ${LEGACY_ERROR_CODES['E001']}`,
          path: ['accountNumber'],
        });
      } else if (parseInt(data.accountNumber, 10) < 100000000) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `[E001] ${LEGACY_ERROR_CODES['E001']}`,
          path: ['accountNumber'],
        });
      }
    }

    // Fund ID validation — BU, SL, TR require it
    if (type !== 'FE') {
      if (!data.fundId || !/^[A-Z0-9]{6}$/.test(data.fundId)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `[E002] ${LEGACY_ERROR_CODES['E002']}`,
          path: ['fundId'],
        });
      }
    }

    // Quantity and Price validation for BU/SL
    if (type === 'BU' || type === 'SL') {
      if (data.quantity === undefined || data.quantity <= 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Quantity must be greater than 0',
          path: ['quantity'],
        });
      }
      if (data.price === undefined || data.price <= 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Price must be greater than 0',
          path: ['price'],
        });
      }
    }

    // Fee amount validation — VAL-INVALID-AMT
    if (type === 'FE') {
      if (data.amount === undefined || data.amount === 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `[VAL-INVALID-AMT] ${LEGACY_ERROR_CODES['VAL-INVALID-AMT']}`,
          path: ['amount'],
        });
      }
    }

    // Transfer account validations
    if (type === 'TR') {
      if (!data.sourceAccount || !/^\d{9}$/.test(data.sourceAccount)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `[E001] ${LEGACY_ERROR_CODES['E001']}`,
          path: ['sourceAccount'],
        });
      } else if (parseInt(data.sourceAccount, 10) < 100000000) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `[E001] ${LEGACY_ERROR_CODES['E001']}`,
          path: ['sourceAccount'],
        });
      }
      if (!data.destinationAccount || !/^\d{9}$/.test(data.destinationAccount)) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `[E001] ${LEGACY_ERROR_CODES['E001']}`,
          path: ['destinationAccount'],
        });
      } else if (parseInt(data.destinationAccount, 10) < 100000000) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `[E001] ${LEGACY_ERROR_CODES['E001']}`,
          path: ['destinationAccount'],
        });
      }
      // Quantity > 0 for transfers
      if (data.quantity === undefined || data.quantity <= 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Quantity must be greater than 0',
          path: ['quantity'],
        });
      }
    }

    // Date must not be in the future
    if (data.transactionDate) {
      const today = new Date();
      today.setHours(23, 59, 59, 999);
      const selectedDate = new Date(data.transactionDate + 'T00:00:00');
      if (selectedDate > today) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Transaction date cannot be in the future',
          path: ['transactionDate'],
        });
      }
    }
  });

type TransactionFormData = z.infer<typeof transactionSchema>;

function getTodayString(): string {
  const now = new Date();
  return (
    now.getFullYear().toString() +
    '-' +
    (now.getMonth() + 1).toString().padStart(2, '0') +
    '-' +
    now.getDate().toString().padStart(2, '0')
  );
}

export default function TransactionSubmit() {
  const history = useHistory();
  const [showConfirm, setShowConfirm] = useState(false);
  const [pendingTransaction, setPendingTransaction] = useState<Transaction | null>(null);
  const [zeroDollarWarning, setZeroDollarWarning] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
    trigger,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } = useForm<TransactionFormData>({
    resolver: zodResolver(transactionSchema) as any,
    mode: 'onBlur',
    defaultValues: {
      transactionType: 'BU',
      currency: 'USD',
      transactionDate: getTodayString(),
      accountNumber: '',
      portfolioId: '',
      fundId: '',
      quantity: undefined,
      price: undefined,
      amount: undefined,
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
  useEffect(() => {
    if (isBuySell) {
      const q = Number(quantity) || 0;
      const p = Number(price) || 0;
      const calculatedAmount = parseFloat((q * p).toFixed(4));
      setValue('amount', calculatedAmount);

      // W001: Zero-dollar warning
      if (q > 0 && p > 0 && calculatedAmount === 0) {
        setZeroDollarWarning(true);
      } else if (calculatedAmount === 0 && (q > 0 || p > 0)) {
        setZeroDollarWarning(true);
      } else {
        setZeroDollarWarning(false);
      }
    } else {
      setZeroDollarWarning(false);
    }
  }, [isBuySell, quantity, price, setValue]);

  const onFormSubmit = (data: TransactionFormData) => {
    const txnId = transactionStore.generateId();
    const transaction: Transaction = {
      transactionId: txnId,
      transactionType: data.transactionType as TransactionType,
      accountNumber: data.transactionType === 'TR' ? (data.sourceAccount ?? '') : (data.accountNumber ?? ''),
      portfolioId: data.portfolioId,
      transactionDate: data.transactionDate,
      fundId: data.fundId ?? '',
      quantity: isBuySell || isTransfer ? (data.quantity ?? 0) : 0,
      price: isBuySell ? (data.price ?? 0) : 0,
      amount: isBuySell ? parseFloat(((data.quantity ?? 0) * (data.price ?? 0)).toFixed(4)) : (data.amount ?? 0),
      currency: data.currency,
      status: 'P',
      sourceAccount: data.sourceAccount,
      destinationAccount: data.destinationAccount,
      description: data.description,
    };

    setPendingTransaction(transaction);
    setShowConfirm(true);
  };

  const handleConfirm = () => {
    if (pendingTransaction) {
      transactionStore.add(pendingTransaction);
      setShowConfirm(false);
      history.push(`${ROUTES.TRANSACTION_STATUS}?highlight=${pendingTransaction.transactionId}`);
    }
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
              <Alert className="bg-yellow-50 border-yellow-300 text-yellow-800 animate-fade-in">
                <strong>[W001]</strong> {LEGACY_ERROR_CODES['W001']}
              </Alert>
            )}

            <Card hover={false} className="animate-fade-in">
              <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
                {/* Transaction Type */}
                <div>
                  <label htmlFor="transactionType" className="block text-sm font-medium mb-1">
                    Transaction Type
                  </label>
                  <select
                    id="transactionType"
                    {...register('transactionType')}
                    onChange={(e) => {
                      setValue('transactionType', e.target.value as TransactionType);
                      trigger('transactionType');
                    }}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                  >
                    {(Object.entries(TRANSACTION_TYPE_LABELS) as [TransactionType, string][]).map(
                      ([value, label]) => (
                        <option key={value} value={value}>
                          {label} ({value})
                        </option>
                      ),
                    )}
                  </select>
                  {errors.transactionType && (
                    <p className="text-sm text-destructive mt-1">{errors.transactionType.message}</p>
                  )}
                </div>

                {/* Account Number — BU, SL, FE */}
                {!isTransfer && (
                  <div>
                    <label htmlFor="accountNumber" className="block text-sm font-medium mb-1">
                      Account Number
                    </label>
                    <Input
                      id="accountNumber"
                      placeholder="9-digit account number"
                      maxLength={9}
                      {...register('accountNumber')}
                      onBlur={() => trigger('accountNumber')}
                    />
                    {errors.accountNumber && (
                      <p className="text-sm text-destructive mt-1">{errors.accountNumber.message}</p>
                    )}
                  </div>
                )}

                {/* Source and Destination Account — TR */}
                {isTransfer && (
                  <>
                    <div>
                      <label htmlFor="sourceAccount" className="block text-sm font-medium mb-1">
                        Source Account
                      </label>
                      <Input
                        id="sourceAccount"
                        placeholder="9-digit source account"
                        maxLength={9}
                        {...register('sourceAccount')}
                        onBlur={() => trigger('sourceAccount')}
                      />
                      {errors.sourceAccount && (
                        <p className="text-sm text-destructive mt-1">{errors.sourceAccount.message}</p>
                      )}
                    </div>
                    <div>
                      <label htmlFor="destinationAccount" className="block text-sm font-medium mb-1">
                        Destination Account
                      </label>
                      <Input
                        id="destinationAccount"
                        placeholder="9-digit destination account"
                        maxLength={9}
                        {...register('destinationAccount')}
                        onBlur={() => trigger('destinationAccount')}
                      />
                      {errors.destinationAccount && (
                        <p className="text-sm text-destructive mt-1">
                          {errors.destinationAccount.message}
                        </p>
                      )}
                    </div>
                  </>
                )}

                {/* Portfolio ID — all types */}
                <div>
                  <label htmlFor="portfolioId" className="block text-sm font-medium mb-1">
                    Portfolio ID
                  </label>
                  <Input
                    id="portfolioId"
                    placeholder="8-char alphanumeric (e.g. PORT0001)"
                    maxLength={8}
                    {...register('portfolioId')}
                    onBlur={() => trigger('portfolioId')}
                  />
                  {errors.portfolioId && (
                    <p className="text-sm text-destructive mt-1">{errors.portfolioId.message}</p>
                  )}
                </div>

                {/* Fund ID — BU, SL, TR */}
                {!isFee && (
                  <div>
                    <label htmlFor="fundId" className="block text-sm font-medium mb-1">
                      Fund ID
                    </label>
                    <Input
                      id="fundId"
                      placeholder="6-char alphanumeric (e.g. AAPL01)"
                      maxLength={6}
                      {...register('fundId')}
                      onBlur={() => trigger('fundId')}
                    />
                    {errors.fundId && (
                      <p className="text-sm text-destructive mt-1">{errors.fundId.message}</p>
                    )}
                  </div>
                )}

                {/* Quantity — BU, SL, TR */}
                {(isBuySell || isTransfer) && (
                  <div>
                    <label htmlFor="quantity" className="block text-sm font-medium mb-1">
                      Quantity
                    </label>
                    <Input
                      id="quantity"
                      type="number"
                      step="0.0001"
                      min="0"
                      placeholder="Enter quantity"
                      {...register('quantity', { valueAsNumber: true })}
                      onBlur={() => trigger('quantity')}
                    />
                    {errors.quantity && (
                      <p className="text-sm text-destructive mt-1">{errors.quantity.message}</p>
                    )}
                  </div>
                )}

                {/* Price — BU, SL only */}
                {isBuySell && (
                  <div>
                    <label htmlFor="price" className="block text-sm font-medium mb-1">
                      Price
                    </label>
                    <Input
                      id="price"
                      type="number"
                      step="0.0001"
                      min="0"
                      placeholder="Enter price per unit"
                      {...register('price', { valueAsNumber: true })}
                      onBlur={() => trigger('price')}
                    />
                    {errors.price && (
                      <p className="text-sm text-destructive mt-1">{errors.price.message}</p>
                    )}
                  </div>
                )}

                {/* Amount — auto-calculated for BU/SL, editable for FE */}
                {(isBuySell || isFee) && (
                  <div>
                    <label htmlFor="amount" className="block text-sm font-medium mb-1">
                      Amount {isBuySell && '(auto-calculated)'}
                    </label>
                    <Input
                      id="amount"
                      type="number"
                      step="0.01"
                      placeholder={isFee ? 'Enter fee amount' : '0.00'}
                      readOnly={isBuySell}
                      {...register('amount', { valueAsNumber: true })}
                      onBlur={() => trigger('amount')}
                      className={isBuySell ? 'bg-muted cursor-not-allowed' : ''}
                    />
                    {errors.amount && (
                      <p className="text-sm text-destructive mt-1">{errors.amount.message}</p>
                    )}
                  </div>
                )}

                {/* Currency — all types */}
                <div>
                  <label htmlFor="currency" className="block text-sm font-medium mb-1">
                    Currency
                  </label>
                  <Input
                    id="currency"
                    placeholder="3-char ISO code (e.g. USD)"
                    maxLength={3}
                    {...register('currency')}
                    onBlur={() => trigger('currency')}
                  />
                  {errors.currency && (
                    <p className="text-sm text-destructive mt-1">{errors.currency.message}</p>
                  )}
                </div>

                {/* Transaction Date — all types */}
                <div>
                  <label htmlFor="transactionDate" className="block text-sm font-medium mb-1">
                    Transaction Date
                  </label>
                  <Input
                    id="transactionDate"
                    type="date"
                    max={getTodayString()}
                    {...register('transactionDate')}
                    onBlur={() => trigger('transactionDate')}
                  />
                  {errors.transactionDate && (
                    <p className="text-sm text-destructive mt-1">{errors.transactionDate.message}</p>
                  )}
                </div>

                {/* Description — FE only */}
                {isFee && (
                  <div>
                    <label htmlFor="description" className="block text-sm font-medium mb-1">
                      Description
                    </label>
                    <Input
                      id="description"
                      placeholder="Fee description"
                      maxLength={50}
                      {...register('description')}
                    />
                  </div>
                )}

                <Button type="submit" className="w-full">
                  Review &amp; Submit
                </Button>
              </form>
            </Card>
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
