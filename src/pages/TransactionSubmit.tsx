import { useState, useEffect } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button, Alert } from '../components';
import { Input } from '../components/ui/input';
import type { TransactionType, Transaction } from '../types/transaction';
import { TRANSACTION_TYPE_LABELS, LEGACY_ERROR_CODES } from '../types/transaction';
import { transactionStore, generateTransactionId } from '../data/mockTransactions';
import TransactionConfirmDialog from '../components/TransactionConfirmDialog';

const transactionTypes: TransactionType[] = ['BU', 'SL', 'TR', 'FE'];

interface FormValues {
  transactionType: string;
  accountNumber: string;
  portfolioId: string;
  transactionDate: string;
  fundId: string;
  quantity: string;
  price: string;
  amount: string;
  currency: string;
  sourceAccount: string;
  destinationAccount: string;
  description: string;
}

function getTodayString(): string {
  const d = new Date();
  return [
    d.getFullYear(),
    String(d.getMonth() + 1).padStart(2, '0'),
    String(d.getDate()).padStart(2, '0'),
  ].join('-');
}


export default function TransactionSubmit() {
  const history = useHistory();
  const [zeroDollarWarning, setZeroDollarWarning] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingTransaction, setPendingTransaction] = useState<Omit<Transaction, 'status'> | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    mode: 'onBlur',
    shouldUnregister: true,
    defaultValues: {
      transactionType: 'BU',
      accountNumber: '',
      portfolioId: '',
      transactionDate: getTodayString(),
      fundId: '',
      quantity: '',
      price: '',
      amount: '',
      currency: 'USD',
      sourceAccount: '',
      destinationAccount: '',
      description: '',
    },
  });

  const transactionType = watch('transactionType') as TransactionType;
  const quantityStr = watch('quantity');
  const priceStr = watch('price');

  const isBuySell = transactionType === 'BU' || transactionType === 'SL';
  const isTransfer = transactionType === 'TR';
  const isFee = transactionType === 'FE';

  useEffect(() => {
    if (isBuySell) {
      const q = parseFloat(quantityStr) || 0;
      const p = parseFloat(priceStr) || 0;
      const calc = parseFloat((q * p).toFixed(4));
      setValue('amount', calc === 0 ? '0' : calc.toString());
      setZeroDollarWarning(calc === 0 && (q > 0 || p > 0));
    } else {
      setZeroDollarWarning(false);
    }
  }, [quantityStr, priceStr, isBuySell, setValue]);

  const onFormSubmit = (data: FormValues) => {
    const txn: Omit<Transaction, 'status'> = {
      transactionId: generateTransactionId(),
      transactionType: data.transactionType as TransactionType,
      accountNumber: isTransfer ? data.sourceAccount : data.accountNumber,
      portfolioId: data.portfolioId,
      transactionDate: data.transactionDate,
      fundId: data.fundId,
      quantity: isFee ? 0 : parseFloat(data.quantity) || 0,
      price: isFee ? 0 : parseFloat(data.price) || 0,
      amount: parseFloat(data.amount) || 0,
      currency: data.currency,
      ...(isTransfer && {
        sourceAccount: data.sourceAccount,
        destinationAccount: data.destinationAccount,
      }),
      ...(isFee && data.description && { description: data.description }),
    };

    setPendingTransaction(txn);
    setConfirmOpen(true);
  };

  const handleConfirm = () => {
    if (!pendingTransaction) return;

    const created = transactionStore.add(pendingTransaction);
    setConfirmOpen(false);
    setPendingTransaction(null);
    history.push(`${ROUTES.TRANSACTION_STATUS}?highlight=${created.transactionId}`);
  };

  const handleCancelConfirm = () => {
    setConfirmOpen(false);
  };

  const fieldError = (name: keyof FormValues) => {
    const err = errors[name];
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
                <strong>W001:</strong> {LEGACY_ERROR_CODES.W001}
              </Alert>
            )}

            <Card hover className="animate-fade-in">
              <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
                {/* Transaction Type */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Transaction Type <span className="text-destructive">*</span>
                  </label>
                  <select
                    {...register('transactionType', {
                      validate: (v) =>
                        ['BU', 'SL', 'TR', 'FE'].includes(v) ||
                        `E003: ${LEGACY_ERROR_CODES.E003}`,
                    })}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] outline-none"
                  >
                    {transactionTypes.map((t) => (
                      <option key={t} value={t}>
                        {TRANSACTION_TYPE_LABELS[t]} ({t})
                      </option>
                    ))}
                  </select>
                  {fieldError('transactionType')}
                </div>

                {/* Account Number (BU, SL, FE) */}
                {!isTransfer && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Account Number <span className="text-destructive">*</span>
                    </label>
                    <Input
                      {...register('accountNumber', {
                        required: 'Account number is required',
                        pattern: {
                          value: /^\d{9}$/,
                          message: `E001: ${LEGACY_ERROR_CODES.E001}`,
                        },
                        validate: (v) =>
                          parseInt(v, 10) >= 100000000 ||
                          `E001: ${LEGACY_ERROR_CODES.E001}`,
                      })}
                      placeholder="9-digit account (e.g. 100000001)"
                      maxLength={9}
                    />
                    {fieldError('accountNumber')}
                  </div>
                )}

                {/* Source + Destination Accounts (TR) */}
                {isTransfer && (
                  <>
                    <div>
                      <label className="block text-sm font-medium mb-1">
                        Source Account <span className="text-destructive">*</span>
                      </label>
                      <Input
                        {...register('sourceAccount', {
                          required: isTransfer ? 'Source account is required' : false,
                          pattern: {
                            value: /^\d{9}$/,
                            message: `E001: ${LEGACY_ERROR_CODES.E001}`,
                          },
                          validate: (v) =>
                            !isTransfer ||
                            parseInt(v, 10) >= 100000000 ||
                            `E001: ${LEGACY_ERROR_CODES.E001}`,
                        })}
                        placeholder="9-digit account (e.g. 100000001)"
                        maxLength={9}
                      />
                      {fieldError('sourceAccount')}
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">
                        Destination Account <span className="text-destructive">*</span>
                      </label>
                      <Input
                        {...register('destinationAccount', {
                          required: isTransfer ? 'Destination account is required' : false,
                          pattern: {
                            value: /^\d{9}$/,
                            message: `E001: ${LEGACY_ERROR_CODES.E001}`,
                          },
                          validate: (v) =>
                            !isTransfer ||
                            parseInt(v, 10) >= 100000000 ||
                            `E001: ${LEGACY_ERROR_CODES.E001}`,
                        })}
                        placeholder="9-digit account (e.g. 100000002)"
                        maxLength={9}
                      />
                      {fieldError('destinationAccount')}
                    </div>
                  </>
                )}

                {/* Portfolio ID */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Portfolio ID <span className="text-destructive">*</span>
                  </label>
                  <Input
                    {...register('portfolioId', {
                      required: 'Portfolio ID is required',
                      pattern: {
                        value: /^[A-Z0-9]{8}$/,
                        message: `VAL-INVALID-ID: ${LEGACY_ERROR_CODES['VAL-INVALID-ID']}`,
                      },
                    })}
                    placeholder="8-char alphanumeric (e.g. PORT0001)"
                    maxLength={8}
                  />
                  {fieldError('portfolioId')}
                </div>

                {/* Fund ID */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Fund ID <span className="text-destructive">*</span>
                  </label>
                  <Input
                    {...register('fundId', {
                      required: 'Fund ID is required',
                      pattern: {
                        value: /^[A-Z0-9]{6}$/,
                        message: `E002: ${LEGACY_ERROR_CODES.E002}`,
                      },
                    })}
                    placeholder="6-char alphanumeric (e.g. AAPL01)"
                    maxLength={6}
                  />
                  {fieldError('fundId')}
                </div>

                {/* Quantity (BU, SL, TR) */}
                {!isFee && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Quantity <span className="text-destructive">*</span>
                    </label>
                    <Input
                      {...register('quantity', {
                        required: !isFee ? 'Quantity is required' : false,
                        validate: (v) => {
                          if (isFee) return true;
                          const n = parseFloat(v);
                          if (isNaN(n)) return 'Quantity must be a number';
                          if (isBuySell && n <= 0) return 'Quantity must be greater than 0';
                          return true;
                        },
                      })}
                      type="number"
                      step="0.0001"
                      min="0"
                      placeholder="e.g. 100.0000"
                    />
                    {fieldError('quantity')}
                  </div>
                )}

                {/* Price (BU, SL) */}
                {isBuySell && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Price <span className="text-destructive">*</span>
                    </label>
                    <Input
                      {...register('price', {
                        required: isBuySell ? 'Price is required' : false,
                        validate: (v) => {
                          if (!isBuySell) return true;
                          const n = parseFloat(v);
                          if (isNaN(n)) return 'Price must be a number';
                          if (n <= 0) return 'Price must be greater than 0';
                          return true;
                        },
                      })}
                      type="number"
                      step="0.0001"
                      min="0"
                      placeholder="e.g. 185.5000"
                    />
                    {fieldError('price')}
                  </div>
                )}

                {/* Amount */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Amount {isFee && <span className="text-destructive">*</span>}
                    {isBuySell && <span className="text-xs text-muted-foreground ml-2">(auto-calculated)</span>}
                  </label>
                  <Input
                    {...register('amount', {
                      validate: (v) => {
                        if (isFee) {
                          const n = parseFloat(v);
                          if (isNaN(n) || n === 0)
                            return `VAL-INVALID-AMT: ${LEGACY_ERROR_CODES['VAL-INVALID-AMT']}`;
                        }
                        return true;
                      },
                    })}
                    type="number"
                    step="0.01"
                    readOnly={isBuySell}
                    className={isBuySell ? 'bg-muted cursor-not-allowed' : ''}
                    placeholder={isFee ? 'Fee amount (non-zero)' : ''}
                  />
                  {fieldError('amount')}
                </div>

                {/* Currency */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Currency <span className="text-destructive">*</span>
                  </label>
                  <Input
                    {...register('currency', {
                      required: 'Currency is required',
                      pattern: {
                        value: /^[A-Z]{3}$/,
                        message: 'Currency must be a 3-letter ISO code',
                      },
                    })}
                    placeholder="3-letter ISO code (e.g. USD)"
                    maxLength={3}
                  />
                  {fieldError('currency')}
                </div>

                {/* Transaction Date */}
                <div>
                  <label className="block text-sm font-medium mb-1">
                    Transaction Date <span className="text-destructive">*</span>
                  </label>
                  <Input
                    {...register('transactionDate', {
                      required: 'Transaction date is required',
                      validate: (v) => {
                        const selected = new Date(v);
                        const today = new Date();
                        today.setHours(23, 59, 59, 999);
                        return selected <= today || 'Transaction date cannot be in the future';
                      },
                    })}
                    type="date"
                    max={getTodayString()}
                  />
                  {fieldError('transactionDate')}
                </div>

                {/* Description (FE only) */}
                {isFee && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Description
                    </label>
                    <Input
                      {...register('description')}
                      placeholder="e.g. Quarterly management fee"
                    />
                    {fieldError('description')}
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
        isOpen={confirmOpen}
        transaction={pendingTransaction}
        onConfirm={handleConfirm}
        onCancel={handleCancelConfirm}
      />
    </div>
  );
}
