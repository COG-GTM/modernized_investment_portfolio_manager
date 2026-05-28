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
import {
  TRANSACTION_TYPE_LABELS,
  LEGACY_ERROR_CODES,
  type TransactionType,
} from '../types/transaction';

// Zod schema with legacy COBOL error code mapping
const baseSchema = z.object({
  transactionType: z.enum(['BU', 'SL', 'TR', 'FE'], {
    message: LEGACY_ERROR_CODES.E003,
  }),
  accountNumber: z
    .string()
    .regex(/^\d{9}$/, LEGACY_ERROR_CODES.E001)
    .refine((v) => parseInt(v, 10) >= 100000000, {
      message: LEGACY_ERROR_CODES.E001,
    }),
  portfolioId: z
    .string()
    .regex(/^[A-Z0-9]{8}$/, LEGACY_ERROR_CODES['VAL-INVALID-ID']),
  fundId: z.string().regex(/^[A-Z0-9]{6}$/, LEGACY_ERROR_CODES.E002),
  transactionDate: z.string().min(1, 'Transaction date is required'),
  quantity: z.number().min(0, 'Quantity must be >= 0'),
  price: z.number().min(0, 'Price must be >= 0'),
  amount: z.number(),
  currency: z
    .string()
    .length(3, 'Currency must be a 3-character ISO code')
    .regex(/^[A-Z]{3}$/, 'Currency must be uppercase letters'),
  sourceAccount: z.string().optional(),
  destinationAccount: z.string().optional(),
  description: z.string().optional(),
});

// Superrefine for conditional rules per transaction type
const transactionSchema = baseSchema.superRefine((data, ctx) => {
  const type = data.transactionType;

  // Date must not be in the future
  if (data.transactionDate) {
    const today = new Date();
    today.setHours(23, 59, 59, 999);
    if (new Date(data.transactionDate) > today) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Transaction date cannot be in the future',
        path: ['transactionDate'],
      });
    }
  }

  // BUY/SELL require quantity > 0 and price > 0
  if (type === 'BU' || type === 'SL') {
    if (data.quantity <= 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Quantity must be greater than 0 for Buy/Sell transactions',
        path: ['quantity'],
      });
    }
    if (data.price <= 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Price must be greater than 0 for Buy/Sell transactions',
        path: ['price'],
      });
    }
  }

  // TRANSFER requires source and destination accounts
  if (type === 'TR') {
    if (!data.sourceAccount || !/^\d{9}$/.test(data.sourceAccount)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: LEGACY_ERROR_CODES.E001,
        path: ['sourceAccount'],
      });
    } else if (parseInt(data.sourceAccount, 10) < 100000000) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: LEGACY_ERROR_CODES.E001,
        path: ['sourceAccount'],
      });
    }
    if (!data.destinationAccount || !/^\d{9}$/.test(data.destinationAccount)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: LEGACY_ERROR_CODES.E001,
        path: ['destinationAccount'],
      });
    } else if (parseInt(data.destinationAccount, 10) < 100000000) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: LEGACY_ERROR_CODES.E001,
        path: ['destinationAccount'],
      });
    }
  }

  // FEE requires non-zero amount
  if (type === 'FE') {
    if (data.amount === 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: LEGACY_ERROR_CODES['VAL-INVALID-AMT'],
        path: ['amount'],
      });
    }
  }
});

interface TransactionFormData {
  transactionType: 'BU' | 'SL' | 'TR' | 'FE';
  accountNumber: string;
  portfolioId: string;
  fundId: string;
  transactionDate: string;
  quantity: number;
  price: number;
  amount: number;
  currency: string;
  sourceAccount?: string;
  destinationAccount?: string;
  description?: string;
}

function getTodayString(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function generatePreviewId(): string {
  const now = new Date();
  const dateStr =
    now.getFullYear().toString() +
    String(now.getMonth() + 1).padStart(2, '0') +
    String(now.getDate()).padStart(2, '0');
  const seq = String(Math.floor(Math.random() * 9000) + 1000);
  return `${dateStr}-${seq}`;
}

export default function TransactionSubmit() {
  const history = useHistory();
  const [showConfirm, setShowConfirm] = useState(false);
  const [zeroDollarWarning, setZeroDollarWarning] = useState(false);
  const [previewId] = useState(generatePreviewId);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<TransactionFormData>({
    resolver: zodResolver(transactionSchema) as any,
    mode: 'onBlur',
    defaultValues: {
      transactionType: 'BU',
      accountNumber: '',
      portfolioId: '',
      fundId: '',
      transactionDate: getTodayString(),
      quantity: 0,
      price: 0,
      amount: 0,
      currency: 'USD',
      sourceAccount: '',
      destinationAccount: '',
      description: '',
    },
  });

  const transactionType = watch('transactionType') as TransactionType;
  const quantity = watch('quantity');
  const price = watch('price');
  const amount = watch('amount');

  const isBuySell = transactionType === 'BU' || transactionType === 'SL';
  const isTransfer = transactionType === 'TR';
  const isFee = transactionType === 'FE';

  // Auto-calculate amount for BUY/SELL
  useEffect(() => {
    if (isBuySell) {
      const q = Number(quantity) || 0;
      const p = Number(price) || 0;
      const calc = parseFloat((q * p).toFixed(2));
      setValue('amount', calc);
    }
  }, [quantity, price, isBuySell, setValue]);

  // W001 zero-dollar warning
  useEffect(() => {
    const currentAmount = isBuySell
      ? parseFloat(((Number(quantity) || 0) * (Number(price) || 0)).toFixed(2))
      : Number(amount) || 0;
    setZeroDollarWarning(currentAmount === 0 && (isBuySell || isFee));
  }, [quantity, price, amount, isBuySell, isFee]);

  const formValues = watch();

  const onFormSubmit = (_data: TransactionFormData) => {
    setShowConfirm(true);
  };

  const onConfirm = () => {
    const newTxn = transactionStore.add({
      transactionType: formValues.transactionType as TransactionType,
      accountNumber: isTransfer
        ? (formValues.sourceAccount ?? '')
        : formValues.accountNumber,
      portfolioId: formValues.portfolioId,
      transactionDate: formValues.transactionDate,
      fundId: formValues.fundId,
      quantity: isFee ? 0 : Number(formValues.quantity),
      price: isFee ? 0 : Number(formValues.price),
      amount: Number(formValues.amount),
      currency: formValues.currency,
      sourceAccount: isTransfer ? formValues.sourceAccount : undefined,
      destinationAccount: isTransfer
        ? formValues.destinationAccount
        : undefined,
      description: isFee ? formValues.description : undefined,
    });
    setShowConfirm(false);
    history.push(
      `${ROUTES.TRANSACTION_STATUS}?highlight=${newTxn.transactionId}`
    );
  };

  const onCancelConfirm = () => {
    setShowConfirm(false);
  };

  const fieldError = (name: keyof TransactionFormData) => {
    const err = errors[name];
    if (!err) return null;
    return (
      <p className="text-sm text-red-600 mt-1">
        {err.message as string}
      </p>
    );
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
            subtitle="Enter transaction details — validation mirrors legacy COBOL rules (TRNVAL00)"
          />

          <main className="space-y-6 animate-slide-up">
            {zeroDollarWarning && (
              <Alert className="border-yellow-300 bg-yellow-50 text-yellow-800 animate-fade-in">
                <strong>W001 Warning:</strong> {LEGACY_ERROR_CODES.W001}.
                Submission is still allowed.
              </Alert>
            )}

            <Card hover={false} className="animate-fade-in">
              <form
                onSubmit={handleSubmit(onFormSubmit)}
                className="space-y-6"
                noValidate
              >
                {/* Transaction Type */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Transaction Type
                  </label>
                  <select
                    {...register('transactionType')}
                    className="w-full h-9 rounded-md border border-input bg-transparent px-3 text-sm focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] outline-none"
                  >
                    {(
                      Object.entries(TRANSACTION_TYPE_LABELS) as [
                        TransactionType,
                        string,
                      ][]
                    ).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label} ({value})
                      </option>
                    ))}
                  </select>
                  {fieldError('transactionType')}
                </div>

                {/* Date */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Transaction Date
                  </label>
                  <Input
                    type="date"
                    max={getTodayString()}
                    {...register('transactionDate')}
                  />
                  {fieldError('transactionDate')}
                </div>

                {/* Account Number — BUY/SELL/FEE */}
                {!isTransfer && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Account Number{' '}
                      <span className="text-muted-foreground text-xs">
                        (9 digits, E001)
                      </span>
                    </label>
                    <Input
                      placeholder="e.g. 100000001"
                      maxLength={9}
                      {...register('accountNumber')}
                    />
                    {fieldError('accountNumber')}
                  </div>
                )}

                {/* Source / Destination Accounts — TRANSFER */}
                {isTransfer && (
                  <>
                    <div>
                      <label className="block text-sm font-medium mb-1">
                        Source Account{' '}
                        <span className="text-muted-foreground text-xs">
                          (9 digits, E001)
                        </span>
                      </label>
                      <Input
                        placeholder="e.g. 100000001"
                        maxLength={9}
                        {...register('sourceAccount')}
                      />
                      {fieldError('sourceAccount')}
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">
                        Destination Account{' '}
                        <span className="text-muted-foreground text-xs">
                          (9 digits, E001)
                        </span>
                      </label>
                      <Input
                        placeholder="e.g. 100000010"
                        maxLength={9}
                        {...register('destinationAccount')}
                      />
                      {fieldError('destinationAccount')}
                    </div>
                  </>
                )}

                {/* Portfolio ID */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Portfolio ID{' '}
                    <span className="text-muted-foreground text-xs">
                      (8-char alphanumeric, VAL-INVALID-ID)
                    </span>
                  </label>
                  <Input
                    placeholder="e.g. PORT0001"
                    maxLength={8}
                    {...register('portfolioId')}
                  />
                  {fieldError('portfolioId')}
                </div>

                {/* Fund ID */}
                {!isFee && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Fund ID{' '}
                      <span className="text-muted-foreground text-xs">
                        (6-char alphanumeric, E002)
                      </span>
                    </label>
                    <Input
                      placeholder="e.g. AAPL01"
                      maxLength={6}
                      {...register('fundId')}
                    />
                    {fieldError('fundId')}
                  </div>
                )}

                {/* Fund ID for FEE — still required by schema but fewer constraints visually */}
                {isFee && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Fund ID{' '}
                      <span className="text-muted-foreground text-xs">
                        (6-char alphanumeric, E002)
                      </span>
                    </label>
                    <Input
                      placeholder="e.g. MGMT01"
                      maxLength={6}
                      {...register('fundId')}
                    />
                    {fieldError('fundId')}
                  </div>
                )}

                {/* Quantity — BUY/SELL/TRANSFER */}
                {!isFee && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Quantity
                    </label>
                    <Input
                      type="number"
                      step="0.0001"
                      min="0"
                      {...register('quantity')}
                    />
                    {fieldError('quantity')}
                  </div>
                )}

                {/* Price — BUY/SELL only */}
                {isBuySell && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Price
                    </label>
                    <Input
                      type="number"
                      step="0.0001"
                      min="0"
                      {...register('price')}
                    />
                    {fieldError('price')}
                  </div>
                )}

                {/* Amount — auto-calculated read-only for BUY/SELL, editable for FEE */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Amount{' '}
                    {isBuySell && (
                      <span className="text-muted-foreground text-xs">
                        (auto-calculated: qty x price)
                      </span>
                    )}
                    {isFee && (
                      <span className="text-muted-foreground text-xs">
                        (VAL-INVALID-AMT: must not be zero)
                      </span>
                    )}
                  </label>
                  <Input
                    type="number"
                    step="0.01"
                    readOnly={isBuySell}
                    className={isBuySell ? 'bg-muted cursor-not-allowed' : ''}
                    {...register('amount')}
                  />
                  {fieldError('amount')}
                </div>

                {/* Currency */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Currency{' '}
                    <span className="text-muted-foreground text-xs">
                      (3-char ISO)
                    </span>
                  </label>
                  <Input
                    placeholder="USD"
                    maxLength={3}
                    {...register('currency')}
                  />
                  {fieldError('currency')}
                </div>

                {/* Description — FEE only */}
                {isFee && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Description
                    </label>
                    <Input
                      placeholder="e.g. Quarterly management fee"
                      {...register('description')}
                    />
                    {fieldError('description')}
                  </div>
                )}

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
        summary={
          showConfirm
            ? {
                transactionId: previewId,
                transactionType:
                  formValues.transactionType as TransactionType,
                accountNumber: isTransfer
                  ? (formValues.sourceAccount ?? '')
                  : formValues.accountNumber,
                portfolioId: formValues.portfolioId,
                transactionDate: formValues.transactionDate,
                fundId: formValues.fundId,
                quantity: isFee ? 0 : Number(formValues.quantity),
                price: isFee ? 0 : Number(formValues.price),
                amount: Number(formValues.amount),
                currency: formValues.currency,
                sourceAccount: isTransfer
                  ? formValues.sourceAccount
                  : undefined,
                destinationAccount: isTransfer
                  ? formValues.destinationAccount
                  : undefined,
                description: isFee ? formValues.description : undefined,
              }
            : null
        }
        onConfirm={onConfirm}
        onCancel={onCancelConfirm}
      />
    </div>
  );
}
