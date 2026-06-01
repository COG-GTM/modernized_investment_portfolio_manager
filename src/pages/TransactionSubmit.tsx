import { useState, useEffect } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button } from '../components';
import { Input } from '../components/ui/input';
import { Alert, AlertTitle, AlertDescription } from '../components/ui/alert';
import { transactionStore } from '../data/mockTransactions';
import {
  TransactionType,
  Transaction,
  TRANSACTION_TYPE_LABELS,
  LEGACY_ERROR_CODES,
} from '../types/transaction';
import TransactionConfirmDialog from '../components/TransactionConfirmDialog';

const transactionTypes: TransactionType[] = ['BU', 'SL', 'TR', 'FE'];

function getTodayString(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function buildSchema(txnType: TransactionType) {
  const base = {
    transactionType: z.enum(['BU', 'SL', 'TR', 'FE'], {
      error: LEGACY_ERROR_CODES['E003'],
    }),
    portfolioId: z
      .string()
      .regex(/^[A-Z0-9]{8}$/, LEGACY_ERROR_CODES['VAL-INVALID-ID']),
    transactionDate: z.string().refine(
      (val) => val <= getTodayString(),
      { message: 'Transaction date cannot be in the future' }
    ),
    currency: z
      .string()
      .regex(/^[A-Z]{3}$/, 'Currency must be a 3-letter ISO code'),
  };

  if (txnType === 'TR') {
    return z.object({
      ...base,
      sourceAccount: z
        .string()
        .regex(/^\d{9}$/, LEGACY_ERROR_CODES['E001'])
        .refine((v) => parseInt(v, 10) >= 100000000, {
          message: LEGACY_ERROR_CODES['E001'],
        }),
      destinationAccount: z
        .string()
        .regex(/^\d{9}$/, LEGACY_ERROR_CODES['E001'])
        .refine((v) => parseInt(v, 10) >= 100000000, {
          message: LEGACY_ERROR_CODES['E001'],
        }),
      fundId: z
        .string()
        .regex(/^[A-Z0-9]{6}$/, LEGACY_ERROR_CODES['E002']),
      quantity: z
        .number({ error: 'Quantity is required' })
        .positive('Quantity must be greater than 0'),
      accountNumber: z.string().optional(),
      price: z.number().optional(),
      amount: z.number().optional(),
      description: z.string().optional(),
    });
  }

  if (txnType === 'FE') {
    return z.object({
      ...base,
      accountNumber: z
        .string()
        .regex(/^\d{9}$/, LEGACY_ERROR_CODES['E001'])
        .refine((v) => parseInt(v, 10) >= 100000000, {
          message: LEGACY_ERROR_CODES['E001'],
        }),
      amount: z
        .number({ error: 'Amount is required' })
        .refine((v) => v !== 0, { message: LEGACY_ERROR_CODES['VAL-INVALID-AMT'] }),
      description: z.string().min(1, 'Description is required for fee transactions'),
      fundId: z.string().optional(),
      quantity: z.number().optional(),
      price: z.number().optional(),
      sourceAccount: z.string().optional(),
      destinationAccount: z.string().optional(),
    });
  }

  // BU or SL
  return z.object({
    ...base,
    accountNumber: z
      .string()
      .regex(/^\d{9}$/, LEGACY_ERROR_CODES['E001'])
      .refine((v) => parseInt(v, 10) >= 100000000, {
        message: LEGACY_ERROR_CODES['E001'],
      }),
    fundId: z
      .string()
      .regex(/^[A-Z0-9]{6}$/, LEGACY_ERROR_CODES['E002']),
    quantity: z
      .number({ error: 'Quantity is required' })
      .positive('Quantity must be greater than 0'),
    price: z
      .number({ error: 'Price is required' })
      .positive('Price must be greater than 0'),
    amount: z.number().optional(),
    description: z.string().optional(),
    sourceAccount: z.string().optional(),
    destinationAccount: z.string().optional(),
  });
}

type FormValues = {
  transactionType: TransactionType;
  accountNumber?: string;
  portfolioId: string;
  transactionDate: string;
  fundId?: string;
  quantity?: number;
  price?: number;
  amount?: number;
  currency: string;
  sourceAccount?: string;
  destinationAccount?: string;
  description?: string;
};

export default function TransactionSubmit() {
  const history = useHistory();
  const [txnType, setTxnType] = useState<TransactionType>('BU');
  const [showConfirm, setShowConfirm] = useState(false);
  const [pendingTransaction, setPendingTransaction] = useState<Omit<Transaction, 'status'> | null>(null);
  const [zeroDollarWarning, setZeroDollarWarning] = useState(false);

  const schema = buildSchema(txnType);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } = useForm<FormValues>({
    resolver: zodResolver(schema) as any,
    mode: 'onBlur',
    defaultValues: {
      transactionType: 'BU',
      transactionDate: getTodayString(),
      currency: 'USD',
      portfolioId: '',
      accountNumber: '',
      fundId: '',
      quantity: undefined,
      price: undefined,
      amount: undefined,
      sourceAccount: '',
      destinationAccount: '',
      description: '',
    },
  });

  const watchQuantity = watch('quantity');
  const watchPrice = watch('price');

  useEffect(() => {
    if (txnType === 'BU' || txnType === 'SL') {
      const q = Number(watchQuantity) || 0;
      const p = Number(watchPrice) || 0;
      const calc = parseFloat((q * p).toFixed(4));
      setValue('amount', calc);
      setZeroDollarWarning(q > 0 && p > 0 && calc === 0);
      if (q > 0 && p > 0 && calc === 0) {
        setZeroDollarWarning(true);
      } else if (calc === 0 && (q > 0 || p > 0)) {
        setZeroDollarWarning(true);
      } else {
        setZeroDollarWarning(false);
      }
    }
  }, [watchQuantity, watchPrice, txnType, setValue]);

  const handleTypeChange = (newType: TransactionType) => {
    setTxnType(newType);
    setZeroDollarWarning(false);
    reset({
      transactionType: newType,
      transactionDate: getTodayString(),
      currency: 'USD',
      portfolioId: '',
      accountNumber: '',
      fundId: '',
      quantity: undefined,
      price: undefined,
      amount: undefined,
      sourceAccount: '',
      destinationAccount: '',
      description: '',
    });
  };

  const onFormSubmit = (data: FormValues) => {
    const now = new Date();
    const dateStr = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`;
    const seq = String(Math.floor(Math.random() * 9000) + 1000).padStart(4, '0');
    const transactionId = `${dateStr}-${seq}`;

    let amount = data.amount || 0;
    if (txnType === 'BU' || txnType === 'SL') {
      amount = parseFloat(((data.quantity || 0) * (data.price || 0)).toFixed(4));
    }

    // Check W001 zero-dollar warning
    if (amount === 0 && (txnType === 'BU' || txnType === 'SL')) {
      setZeroDollarWarning(true);
    }

    const transaction: Omit<Transaction, 'status'> = {
      transactionId,
      transactionType: data.transactionType,
      accountNumber: data.accountNumber || data.sourceAccount || '',
      portfolioId: data.portfolioId,
      transactionDate: data.transactionDate,
      fundId: data.fundId || '',
      quantity: data.quantity || 0,
      price: data.price || 0,
      amount,
      currency: data.currency,
      sourceAccount: data.sourceAccount,
      destinationAccount: data.destinationAccount,
      description: data.description,
    };

    setPendingTransaction(transaction);
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

  const isBuySell = txnType === 'BU' || txnType === 'SL';
  const isTransfer = txnType === 'TR';
  const isFee = txnType === 'FE';

  const getFieldError = (field: string): string | undefined => {
    const err = (errors as Record<string, { message?: string }>)[field];
    return err?.message;
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
              <Alert className="border-yellow-300 bg-yellow-50 text-yellow-800 animate-fade-in">
                <AlertTitle>Warning (W001)</AlertTitle>
                <AlertDescription>
                  {LEGACY_ERROR_CODES['W001']}
                </AlertDescription>
              </Alert>
            )}

            <Card hover className="animate-fade-in">
              <form onSubmit={handleSubmit(onFormSubmit as any)} className="space-y-6">
                <h2 className="text-2xl font-semibold mb-4">Transaction Entry</h2>

                {/* Transaction Type */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Transaction Type <span className="text-red-500">*</span>
                  </label>
                  <select
                    {...register('transactionType')}
                    value={txnType}
                    onChange={(e) => handleTypeChange(e.target.value as TransactionType)}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs transition-colors focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] outline-none"
                  >
                    {transactionTypes.map((t) => (
                      <option key={t} value={t}>
                        {TRANSACTION_TYPE_LABELS[t]} ({t})
                      </option>
                    ))}
                  </select>
                  {getFieldError('transactionType') && (
                    <p className="text-sm text-red-500 mt-1">[E003] {getFieldError('transactionType')}</p>
                  )}
                </div>

                {/* Date */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Transaction Date <span className="text-red-500">*</span>
                  </label>
                  <Input
                    type="date"
                    {...register('transactionDate')}
                    max={getTodayString()}
                  />
                  {getFieldError('transactionDate') && (
                    <p className="text-sm text-red-500 mt-1">{getFieldError('transactionDate')}</p>
                  )}
                </div>

                {/* Account Number (BU/SL/FE) */}
                {!isTransfer && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Account Number <span className="text-red-500">*</span>
                    </label>
                    <Input
                      type="text"
                      placeholder="9-digit account (e.g., 100000001)"
                      maxLength={9}
                      {...register('accountNumber')}
                    />
                    {getFieldError('accountNumber') && (
                      <p className="text-sm text-red-500 mt-1">[E001] {getFieldError('accountNumber')}</p>
                    )}
                  </div>
                )}

                {/* Source / Destination Account (TR) */}
                {isTransfer && (
                  <>
                    <div>
                      <label className="block text-sm font-medium mb-1">
                        Source Account <span className="text-red-500">*</span>
                      </label>
                      <Input
                        type="text"
                        placeholder="9-digit account (e.g., 100000001)"
                        maxLength={9}
                        {...register('sourceAccount')}
                      />
                      {getFieldError('sourceAccount') && (
                        <p className="text-sm text-red-500 mt-1">[E001] {getFieldError('sourceAccount')}</p>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">
                        Destination Account <span className="text-red-500">*</span>
                      </label>
                      <Input
                        type="text"
                        placeholder="9-digit account (e.g., 100000002)"
                        maxLength={9}
                        {...register('destinationAccount')}
                      />
                      {getFieldError('destinationAccount') && (
                        <p className="text-sm text-red-500 mt-1">[E001] {getFieldError('destinationAccount')}</p>
                      )}
                    </div>
                  </>
                )}

                {/* Portfolio ID */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Portfolio ID <span className="text-red-500">*</span>
                  </label>
                  <Input
                    type="text"
                    placeholder="8-char alphanumeric (e.g., PORT0001)"
                    maxLength={8}
                    {...register('portfolioId')}
                  />
                  {getFieldError('portfolioId') && (
                    <p className="text-sm text-red-500 mt-1">[VAL-INVALID-ID] {getFieldError('portfolioId')}</p>
                  )}
                </div>

                {/* Fund ID (BU/SL/TR) */}
                {!isFee && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Fund ID <span className="text-red-500">*</span>
                    </label>
                    <Input
                      type="text"
                      placeholder="6-char alphanumeric (e.g., AAPL01)"
                      maxLength={6}
                      {...register('fundId')}
                    />
                    {getFieldError('fundId') && (
                      <p className="text-sm text-red-500 mt-1">[E002] {getFieldError('fundId')}</p>
                    )}
                  </div>
                )}

                {/* Quantity (BU/SL/TR) */}
                {!isFee && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Quantity <span className="text-red-500">*</span>
                    </label>
                    <Input
                      type="number"
                      step="0.0001"
                      placeholder="0.0000"
                      {...register('quantity', { valueAsNumber: true })}
                    />
                    {getFieldError('quantity') && (
                      <p className="text-sm text-red-500 mt-1">{getFieldError('quantity')}</p>
                    )}
                  </div>
                )}

                {/* Price (BU/SL only) */}
                {isBuySell && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Price <span className="text-red-500">*</span>
                    </label>
                    <Input
                      type="number"
                      step="0.0001"
                      placeholder="0.0000"
                      {...register('price', { valueAsNumber: true })}
                    />
                    {getFieldError('price') && (
                      <p className="text-sm text-red-500 mt-1">{getFieldError('price')}</p>
                    )}
                  </div>
                )}

                {/* Amount (auto-calc for BU/SL, editable for FE) */}
                {(isBuySell || isFee) && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Amount {isBuySell && <span className="text-muted-foreground">(auto-calculated)</span>}
                      {isFee && <span className="text-red-500">*</span>}
                    </label>
                    {isBuySell ? (
                      <Input
                        type="number"
                        step="0.0001"
                        readOnly
                        className="bg-muted"
                        {...register('amount', { valueAsNumber: true })}
                      />
                    ) : (
                      <Input
                        type="number"
                        step="0.01"
                        placeholder="0.00"
                        {...register('amount', { valueAsNumber: true })}
                      />
                    )}
                    {getFieldError('amount') && (
                      <p className="text-sm text-red-500 mt-1">[VAL-INVALID-AMT] {getFieldError('amount')}</p>
                    )}
                  </div>
                )}

                {/* Currency */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Currency <span className="text-red-500">*</span>
                  </label>
                  <Input
                    type="text"
                    placeholder="3-letter ISO (e.g., USD)"
                    maxLength={3}
                    {...register('currency')}
                  />
                  {getFieldError('currency') && (
                    <p className="text-sm text-red-500 mt-1">{getFieldError('currency')}</p>
                  )}
                </div>

                {/* Description (FE only) */}
                {isFee && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Description <span className="text-red-500">*</span>
                    </label>
                    <Input
                      type="text"
                      placeholder="Fee description"
                      {...register('description')}
                    />
                    {getFieldError('description') && (
                      <p className="text-sm text-red-500 mt-1">{getFieldError('description')}</p>
                    )}
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
        transaction={pendingTransaction}
        onConfirm={handleConfirm}
        onCancel={handleCancelConfirm}
      />
    </div>
  );
}
