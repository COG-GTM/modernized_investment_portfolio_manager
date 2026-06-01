import { useState, useMemo, useEffect } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button, Alert } from '../components';
import { Input } from '../components/ui/input';
import TransactionConfirmDialog from '../components/TransactionConfirmDialog';
import {
  TransactionType,
  Transaction,
  TRANSACTION_TYPE_LABELS,
  LEGACY_ERROR_CODES,
} from '../types/transaction';
import { transactionStore } from '../data/mockTransactions';

// --- Zod schema with legacy error code mapping ---

const TRANSACTION_TYPES: [string, ...string[]] = ['BU', 'SL', 'TR', 'FE'];

const baseSchema = z.object({
  transactionType: z.enum(TRANSACTION_TYPES, {
    error: `E003: ${LEGACY_ERROR_CODES['E003']}`,
  }),
  accountNumber: z
    .string()
    .regex(/^\d{9}$/, { message: `E001: ${LEGACY_ERROR_CODES['E001']}` })
    .refine((val) => parseInt(val, 10) >= 100000000, {
      message: `E001: ${LEGACY_ERROR_CODES['E001']}`,
    }),
  portfolioId: z
    .string()
    .regex(/^[A-Z0-9]{8}$/, { message: `VAL-INVALID-ID: ${LEGACY_ERROR_CODES['VAL-INVALID-ID']}` }),
  fundId: z.string(),
  quantity: z.number(),
  price: z.number(),
  amount: z.number(),
  currency: z.string().regex(/^[A-Z]{3}$/, { message: 'Currency must be a 3-letter ISO code' }),
  transactionDate: z.string().min(1, { message: 'Date is required' }),
  sourceAccount: z.string().optional(),
  destinationAccount: z.string().optional(),
  description: z.string().optional(),
});

// We apply conditional refinements after the base schema
const transactionFormSchema = baseSchema.superRefine((data, ctx) => {
  const type = data.transactionType as TransactionType;

  // Fund ID validation for BU/SL/TR
  if (type === 'BU' || type === 'SL' || type === 'TR') {
    if (!/^[A-Z0-9]{6}$/.test(data.fundId)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: `E002: ${LEGACY_ERROR_CODES['E002']}`,
        path: ['fundId'],
      });
    }
  }

  // Quantity > 0 for BU/SL
  if (type === 'BU' || type === 'SL') {
    if (data.quantity <= 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Quantity must be greater than 0',
        path: ['quantity'],
      });
    }
    if (data.price <= 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Price must be greater than 0',
        path: ['price'],
      });
    }
  }

  // Amount != 0 for FE
  if (type === 'FE') {
    if (data.amount === 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: `VAL-INVALID-AMT: ${LEGACY_ERROR_CODES['VAL-INVALID-AMT']}`,
        path: ['amount'],
      });
    }
  }

  // Transfer: source and destination accounts required, valid 9-digit
  if (type === 'TR') {
    if (!data.sourceAccount || !/^\d{9}$/.test(data.sourceAccount) || parseInt(data.sourceAccount, 10) < 100000000) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: `E001: ${LEGACY_ERROR_CODES['E001']}`,
        path: ['sourceAccount'],
      });
    }
    if (!data.destinationAccount || !/^\d{9}$/.test(data.destinationAccount) || parseInt(data.destinationAccount, 10) < 100000000) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: `E001: ${LEGACY_ERROR_CODES['E001']}`,
        path: ['destinationAccount'],
      });
    }
  }

  // Date <= today
  if (data.transactionDate) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const txDate = new Date(data.transactionDate + 'T00:00:00');
    if (txDate > today) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Transaction date cannot be in the future',
        path: ['transactionDate'],
      });
    }
  }
});

type FormData = z.infer<typeof baseSchema>;

function getTodayString(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
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
  } = useForm<FormData>({
    resolver: zodResolver(transactionFormSchema),
    mode: 'onBlur',
    defaultValues: {
      transactionType: 'BU',
      accountNumber: '',
      portfolioId: '',
      fundId: '',
      quantity: 0,
      price: 0,
      amount: 0,
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

  // Auto-calculate amount for BU/SL
  const calculatedAmount = useMemo(() => {
    if (isBuySell) {
      return Number((quantity * price).toFixed(4));
    }
    return 0;
  }, [isBuySell, quantity, price]);

  // Sync calculated amount into the form when quantity/price change
  useEffect(() => {
    if (isBuySell) {
      setValue('amount', calculatedAmount);
      setZeroDollarWarning(calculatedAmount === 0 && (quantity > 0 || price > 0));
    }
  }, [isBuySell, calculatedAmount, quantity, price, setValue]);

  const onFormSubmit = (data: FormData) => {
    const txId = transactionStore.generateTransactionId();
    const amount = isBuySell ? calculatedAmount : data.amount;

    // Check W001: zero-dollar warning
    if (isBuySell && amount === 0) {
      setZeroDollarWarning(true);
    }

    const transaction: Transaction = {
      transactionId: txId,
      transactionType: data.transactionType as TransactionType,
      accountNumber: isTransfer ? (data.sourceAccount || '') : data.accountNumber,
      portfolioId: data.portfolioId,
      transactionDate: data.transactionDate,
      fundId: data.fundId,
      quantity: isFee ? 0 : data.quantity,
      price: isFee ? 0 : (isTransfer ? 0 : data.price),
      amount,
      currency: data.currency,
      status: 'P',
      sourceAccount: isTransfer ? data.sourceAccount : undefined,
      destinationAccount: isTransfer ? data.destinationAccount : undefined,
      description: isFee ? data.description : undefined,
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

  const handleBlur = (field: keyof FormData) => {
    trigger(field);
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
                <strong>W001:</strong> {LEGACY_ERROR_CODES['W001']}
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
                    onBlur={() => handleBlur('transactionType')}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
                  >
                    {(Object.keys(TRANSACTION_TYPE_LABELS) as TransactionType[]).map((key) => (
                      <option key={key} value={key}>
                        {TRANSACTION_TYPE_LABELS[key]} ({key})
                      </option>
                    ))}
                  </select>
                  {errors.transactionType && (
                    <p className="text-sm text-destructive mt-1">{errors.transactionType.message}</p>
                  )}
                </div>

                {/* Account Number — shown for BU/SL/FE */}
                {!isTransfer && (
                  <div>
                    <label htmlFor="accountNumber" className="block text-sm font-medium mb-1">
                      Account Number
                    </label>
                    <Input
                      id="accountNumber"
                      placeholder="123456789"
                      maxLength={9}
                      {...register('accountNumber')}
                      onBlur={() => handleBlur('accountNumber')}
                      aria-invalid={!!errors.accountNumber}
                    />
                    {errors.accountNumber && (
                      <p className="text-sm text-destructive mt-1">{errors.accountNumber.message}</p>
                    )}
                  </div>
                )}

                {/* Source Account — Transfer only */}
                {isTransfer && (
                  <div>
                    <label htmlFor="sourceAccount" className="block text-sm font-medium mb-1">
                      Source Account
                    </label>
                    <Input
                      id="sourceAccount"
                      placeholder="123456789"
                      maxLength={9}
                      {...register('sourceAccount')}
                      onBlur={() => handleBlur('sourceAccount')}
                      aria-invalid={!!errors.sourceAccount}
                    />
                    {errors.sourceAccount && (
                      <p className="text-sm text-destructive mt-1">{errors.sourceAccount.message}</p>
                    )}
                  </div>
                )}

                {/* Destination Account — Transfer only */}
                {isTransfer && (
                  <div>
                    <label htmlFor="destinationAccount" className="block text-sm font-medium mb-1">
                      Destination Account
                    </label>
                    <Input
                      id="destinationAccount"
                      placeholder="123456789"
                      maxLength={9}
                      {...register('destinationAccount')}
                      onBlur={() => handleBlur('destinationAccount')}
                      aria-invalid={!!errors.destinationAccount}
                    />
                    {errors.destinationAccount && (
                      <p className="text-sm text-destructive mt-1">{errors.destinationAccount.message}</p>
                    )}
                  </div>
                )}

                {/* Portfolio ID */}
                <div>
                  <label htmlFor="portfolioId" className="block text-sm font-medium mb-1">
                    Portfolio ID
                  </label>
                  <Input
                    id="portfolioId"
                    placeholder="PORT0001"
                    maxLength={8}
                    {...register('portfolioId')}
                    onBlur={() => handleBlur('portfolioId')}
                    aria-invalid={!!errors.portfolioId}
                  />
                  {errors.portfolioId && (
                    <p className="text-sm text-destructive mt-1">{errors.portfolioId.message}</p>
                  )}
                </div>

                {/* Fund ID — BU/SL/TR only */}
                {!isFee && (
                  <div>
                    <label htmlFor="fundId" className="block text-sm font-medium mb-1">
                      Fund ID
                    </label>
                    <Input
                      id="fundId"
                      placeholder="AAPL01"
                      maxLength={6}
                      {...register('fundId')}
                      onBlur={() => handleBlur('fundId')}
                      aria-invalid={!!errors.fundId}
                    />
                    {errors.fundId && (
                      <p className="text-sm text-destructive mt-1">{errors.fundId.message}</p>
                    )}
                  </div>
                )}

                {/* Quantity — BU/SL/TR */}
                {!isFee && (
                  <div>
                    <label htmlFor="quantity" className="block text-sm font-medium mb-1">
                      Quantity
                    </label>
                    <Input
                      id="quantity"
                      type="number"
                      step="0.0001"
                      min="0"
                      {...register('quantity', { valueAsNumber: true })}
                      onBlur={() => handleBlur('quantity')}
                      aria-invalid={!!errors.quantity}
                    />
                    {errors.quantity && (
                      <p className="text-sm text-destructive mt-1">{errors.quantity.message}</p>
                    )}
                  </div>
                )}

                {/* Price — BU/SL only */}
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
                      {...register('price', { valueAsNumber: true })}
                      onBlur={() => handleBlur('price')}
                      aria-invalid={!!errors.price}
                    />
                    {errors.price && (
                      <p className="text-sm text-destructive mt-1">{errors.price.message}</p>
                    )}
                  </div>
                )}

                {/* Amount — read-only for BU/SL, editable for FE */}
                {(isBuySell || isFee) && (
                  <div>
                    <label htmlFor="amount" className="block text-sm font-medium mb-1">
                      Amount {isBuySell && <span className="text-muted-foreground">(auto-calculated)</span>}
                    </label>
                    {isBuySell ? (
                      <Input
                        id="amount"
                        type="text"
                        readOnly
                        value={`$${calculatedAmount.toFixed(2)}`}
                        className="bg-muted cursor-not-allowed"
                      />
                    ) : (
                      <>
                        <Input
                          id="amount"
                          type="number"
                          step="0.01"
                          {...register('amount', { valueAsNumber: true })}
                          onBlur={() => handleBlur('amount')}
                          aria-invalid={!!errors.amount}
                        />
                        {errors.amount && (
                          <p className="text-sm text-destructive mt-1">{errors.amount.message}</p>
                        )}
                      </>
                    )}
                  </div>
                )}

                {/* Currency */}
                <div>
                  <label htmlFor="currency" className="block text-sm font-medium mb-1">
                    Currency
                  </label>
                  <Input
                    id="currency"
                    placeholder="USD"
                    maxLength={3}
                    {...register('currency')}
                    onBlur={() => handleBlur('currency')}
                    aria-invalid={!!errors.currency}
                  />
                  {errors.currency && (
                    <p className="text-sm text-destructive mt-1">{errors.currency.message}</p>
                  )}
                </div>

                {/* Transaction Date */}
                <div>
                  <label htmlFor="transactionDate" className="block text-sm font-medium mb-1">
                    Transaction Date
                  </label>
                  <Input
                    id="transactionDate"
                    type="date"
                    {...register('transactionDate')}
                    onBlur={() => handleBlur('transactionDate')}
                    aria-invalid={!!errors.transactionDate}
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
                      {...register('description')}
                      onBlur={() => handleBlur('description')}
                    />
                  </div>
                )}

                {/* Submit */}
                <div className="flex gap-3 pt-2">
                  <Button type="submit" className="flex-1">
                    Review &amp; Submit
                  </Button>
                  <Link to={ROUTES.TRANSACTION_STATUS}>
                    <Button type="button" variant="outline">
                      View Status
                    </Button>
                  </Link>
                </div>
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
