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
  TransactionType,
  Transaction,
  TRANSACTION_TYPE_LABELS,
  LEGACY_ERROR_CODES,
} from '../types/transaction';

const transactionTypes: TransactionType[] = ['BU', 'SL', 'TR', 'FE'];

const baseSchema = z.object({
  transactionType: z.enum(['BU', 'SL', 'TR', 'FE'], {
    message: LEGACY_ERROR_CODES.E003,
  }),
  accountNumber: z.string().optional(),
  portfolioId: z
    .string()
    .regex(/^[A-Z0-9]{8}$/, LEGACY_ERROR_CODES['VAL-INVALID-ID']),
  transactionDate: z.string().refine(
    (val) => {
      if (!val) return false;
      const selected = new Date(val + 'T00:00:00');
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      return selected <= today;
    },
    { message: 'Date must not be in the future' }
  ),
  fundId: z.string().optional(),
  quantity: z.number().optional(),
  price: z.number().optional(),
  feeAmount: z.number().optional(),
  currency: z
    .string()
    .length(3, 'Currency must be a 3-character ISO code'),
  sourceAccount: z.string().optional(),
  destinationAccount: z.string().optional(),
  description: z.string().optional(),
});

type FormValues = z.infer<typeof baseSchema>;

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
  const [pendingTransactionData, setPendingTransactionData] = useState<Omit<Transaction, 'status'> | null>(null);
  const [customErrors, setCustomErrors] = useState<Record<string, string>>({});

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
    trigger,
  } = useForm<FormValues>({
    resolver: zodResolver(baseSchema),
    mode: 'onBlur',
    defaultValues: {
      transactionType: 'BU',
      accountNumber: '',
      portfolioId: '',
      transactionDate: getTodayString(),
      fundId: '',
      quantity: undefined,
      price: undefined,
      feeAmount: undefined,
      currency: 'USD',
      sourceAccount: '',
      destinationAccount: '',
      description: '',
    },
  });

  const txnType = watch('transactionType') as TransactionType;
  const quantity = watch('quantity');
  const price = watch('price');

  const isBuyOrSell = txnType === 'BU' || txnType === 'SL';
  const isTransfer = txnType === 'TR';
  const isFee = txnType === 'FE';

  const calculatedAmount = (isBuyOrSell || isTransfer) ? (quantity ?? 0) * (price ?? 0) : 0;

  useEffect(() => {
    if (isBuyOrSell && quantity != null && price != null) {
      setZeroDollarWarning(calculatedAmount === 0);
    } else {
      setZeroDollarWarning(false);
    }
  }, [quantity, price, calculatedAmount, isBuyOrSell]);

  function validateCustomRules(data: FormValues): Record<string, string> {
    const errs: Record<string, string> = {};

    if (!isTransfer) {
      const acct = data.accountNumber ?? '';
      if (!/^\d{9}$/.test(acct) || parseInt(acct, 10) < 100000000) {
        errs.accountNumber = `E001: ${LEGACY_ERROR_CODES.E001}`;
      }
    }

    if (isTransfer) {
      const src = data.sourceAccount ?? '';
      if (!/^\d{9}$/.test(src) || parseInt(src, 10) < 100000000) {
        errs.sourceAccount = `E001: ${LEGACY_ERROR_CODES.E001}`;
      }
      const dst = data.destinationAccount ?? '';
      if (!/^\d{9}$/.test(dst) || parseInt(dst, 10) < 100000000) {
        errs.destinationAccount = `E001: ${LEGACY_ERROR_CODES.E001}`;
      }
    }

    if (!isFee) {
      const fid = data.fundId ?? '';
      if (!/^[A-Z0-9]{6}$/.test(fid)) {
        errs.fundId = `E002: ${LEGACY_ERROR_CODES.E002}`;
      }
    }

    if (isBuyOrSell) {
      if (!data.quantity || data.quantity <= 0) {
        errs.quantity = 'Quantity must be greater than 0';
      }
      if (!data.price || data.price <= 0) {
        errs.price = 'Price must be greater than 0';
      }
    }

    return errs;
  }

  function onFormSubmit(data: FormValues) {
    const customErrs = validateCustomRules(data);
    if (Object.keys(customErrs).length > 0) {
      setCustomErrors(customErrs);
      return;
    }
    setCustomErrors({});

    let amount: number;
    if (isBuyOrSell) {
      amount = (data.quantity ?? 0) * (data.price ?? 0);
    } else if (isTransfer) {
      amount = (data.quantity ?? 0) * (data.price ?? 0);
    } else {
      amount = data.feeAmount ?? 0;
    }

    if (isFee && amount === 0) {
      setCustomErrors({
        feeAmount: `VAL-INVALID-AMT: ${LEGACY_ERROR_CODES['VAL-INVALID-AMT']}`,
      });
      return;
    }

    const txn: Omit<Transaction, 'status'> = {
      transactionId: '',
      transactionType: data.transactionType as TransactionType,
      accountNumber: isTransfer
        ? (data.sourceAccount ?? '')
        : (data.accountNumber ?? ''),
      portfolioId: data.portfolioId,
      transactionDate: data.transactionDate,
      fundId: isFee ? '' : (data.fundId ?? ''),
      quantity: isFee ? 0 : (data.quantity ?? 0),
      price: (isBuyOrSell || isTransfer) ? (data.price ?? 0) : 0,
      amount: parseFloat(amount.toFixed(2)),
      currency: data.currency,
      sourceAccount: isTransfer ? data.sourceAccount : undefined,
      destinationAccount: isTransfer ? data.destinationAccount : undefined,
      description: isFee ? data.description : undefined,
    };

    if (isBuyOrSell && amount === 0) {
      setZeroDollarWarning(true);
    }

    setPendingTransactionData(txn);
    setConfirmOpen(true);
  }

  function handleConfirm() {
    if (!pendingTransactionData) return;
    const created = transactionStore.add(pendingTransactionData);
    setConfirmOpen(false);
    setPendingTransactionData(null);
    history.push(
      `${ROUTES.TRANSACTION_STATUS}?highlight=${created.transactionId}`
    );
  }

  function handleCancelConfirm() {
    setConfirmOpen(false);
    setPendingTransactionData(null);
  }

  function fieldError(field: string): string | undefined {
    return (
      customErrors[field] ||
      (errors as Record<string, { message?: string }>)[field]?.message
    );
  }

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
                <strong>W001:</strong> {LEGACY_ERROR_CODES.W001}
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
                  <label
                    htmlFor="transactionType"
                    className="block text-sm font-medium mb-1"
                  >
                    Transaction Type
                  </label>
                  <select
                    id="transactionType"
                    {...register('transactionType')}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] outline-none"
                    onBlur={() => trigger('transactionType')}
                  >
                    {transactionTypes.map((t) => (
                      <option key={t} value={t}>
                        {TRANSACTION_TYPE_LABELS[t]} ({t})
                      </option>
                    ))}
                  </select>
                  <FieldError message={fieldError('transactionType')} />
                </div>

                {/* Account Number — BUY/SELL/FEE */}
                {!isTransfer && (
                  <div>
                    <label
                      htmlFor="accountNumber"
                      className="block text-sm font-medium mb-1"
                    >
                      Account Number
                    </label>
                    <Input
                      id="accountNumber"
                      placeholder="9-digit account (e.g. 100000001)"
                      maxLength={9}
                      {...register('accountNumber')}
                      onBlur={() => {
                        trigger('accountNumber');
                        const val = watch('accountNumber') ?? '';
                        if (val && (!/^\d{9}$/.test(val) || parseInt(val, 10) < 100000000)) {
                          setCustomErrors((prev) => ({
                            ...prev,
                            accountNumber: `E001: ${LEGACY_ERROR_CODES.E001}`,
                          }));
                        } else {
                          setCustomErrors((prev) => {
                            const next = { ...prev };
                            delete next.accountNumber;
                            return next;
                          });
                        }
                      }}
                      aria-invalid={!!fieldError('accountNumber')}
                    />
                    <FieldError message={fieldError('accountNumber')} />
                  </div>
                )}

                {/* Source / Destination — TRANSFER */}
                {isTransfer && (
                  <>
                    <div>
                      <label
                        htmlFor="sourceAccount"
                        className="block text-sm font-medium mb-1"
                      >
                        Source Account
                      </label>
                      <Input
                        id="sourceAccount"
                        placeholder="9-digit account"
                        maxLength={9}
                        {...register('sourceAccount')}
                        onBlur={() => {
                          const val = watch('sourceAccount') ?? '';
                          if (val && (!/^\d{9}$/.test(val) || parseInt(val, 10) < 100000000)) {
                            setCustomErrors((prev) => ({
                              ...prev,
                              sourceAccount: `E001: ${LEGACY_ERROR_CODES.E001}`,
                            }));
                          } else {
                            setCustomErrors((prev) => {
                              const next = { ...prev };
                              delete next.sourceAccount;
                              return next;
                            });
                          }
                        }}
                        aria-invalid={!!fieldError('sourceAccount')}
                      />
                      <FieldError message={fieldError('sourceAccount')} />
                    </div>
                    <div>
                      <label
                        htmlFor="destinationAccount"
                        className="block text-sm font-medium mb-1"
                      >
                        Destination Account
                      </label>
                      <Input
                        id="destinationAccount"
                        placeholder="9-digit account"
                        maxLength={9}
                        {...register('destinationAccount')}
                        onBlur={() => {
                          const val = watch('destinationAccount') ?? '';
                          if (val && (!/^\d{9}$/.test(val) || parseInt(val, 10) < 100000000)) {
                            setCustomErrors((prev) => ({
                              ...prev,
                              destinationAccount: `E001: ${LEGACY_ERROR_CODES.E001}`,
                            }));
                          } else {
                            setCustomErrors((prev) => {
                              const next = { ...prev };
                              delete next.destinationAccount;
                              return next;
                            });
                          }
                        }}
                        aria-invalid={!!fieldError('destinationAccount')}
                      />
                      <FieldError message={fieldError('destinationAccount')} />
                    </div>
                  </>
                )}

                {/* Portfolio ID */}
                <div>
                  <label
                    htmlFor="portfolioId"
                    className="block text-sm font-medium mb-1"
                  >
                    Portfolio ID
                  </label>
                  <Input
                    id="portfolioId"
                    placeholder="8-character alphanumeric (e.g. PORT0001)"
                    maxLength={8}
                    {...register('portfolioId')}
                    onBlur={() => trigger('portfolioId')}
                    aria-invalid={!!fieldError('portfolioId')}
                  />
                  <FieldError message={fieldError('portfolioId')} />
                </div>

                {/* Fund ID — BUY/SELL/TRANSFER */}
                {!isFee && (
                  <div>
                    <label
                      htmlFor="fundId"
                      className="block text-sm font-medium mb-1"
                    >
                      Fund ID
                    </label>
                    <Input
                      id="fundId"
                      placeholder="6-character alphanumeric (e.g. AAPL01)"
                      maxLength={6}
                      {...register('fundId')}
                      onBlur={() => {
                        trigger('fundId');
                        const val = watch('fundId') ?? '';
                        if (val && !/^[A-Z0-9]{6}$/.test(val)) {
                          setCustomErrors((prev) => ({
                            ...prev,
                            fundId: `E002: ${LEGACY_ERROR_CODES.E002}`,
                          }));
                        } else {
                          setCustomErrors((prev) => {
                            const next = { ...prev };
                            delete next.fundId;
                            return next;
                          });
                        }
                      }}
                      aria-invalid={!!fieldError('fundId')}
                    />
                    <FieldError message={fieldError('fundId')} />
                  </div>
                )}

                {/* Quantity — BUY/SELL/TRANSFER */}
                {!isFee && (
                  <div>
                    <label
                      htmlFor="quantity"
                      className="block text-sm font-medium mb-1"
                    >
                      Quantity
                    </label>
                    <Input
                      id="quantity"
                      type="number"
                      step="0.0001"
                      min="0"
                      placeholder="0.0000"
                      {...register('quantity', { valueAsNumber: true })}
                      onBlur={() => trigger('quantity')}
                      aria-invalid={!!fieldError('quantity')}
                    />
                    <FieldError message={fieldError('quantity')} />
                  </div>
                )}

                {/* Price — BUY/SELL/TRANSFER */}
                {(isBuyOrSell || isTransfer) && (
                  <div>
                    <label
                      htmlFor="price"
                      className="block text-sm font-medium mb-1"
                    >
                      Price
                    </label>
                    <Input
                      id="price"
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="0.00"
                      {...register('price', { valueAsNumber: true })}
                      onBlur={() => trigger('price')}
                      aria-invalid={!!fieldError('price')}
                    />
                    <FieldError message={fieldError('price')} />
                  </div>
                )}

                {/* Amount — auto-calc for BUY/SELL/TRANSFER, editable for FEE */}
                {(isBuyOrSell || isTransfer) && (
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Amount (auto-calculated)
                    </label>
                    <Input
                      readOnly
                      value={`$${calculatedAmount.toFixed(2)}`}
                      className="bg-muted cursor-not-allowed"
                      tabIndex={-1}
                    />
                  </div>
                )}

                {isFee && (
                  <div>
                    <label
                      htmlFor="feeAmount"
                      className="block text-sm font-medium mb-1"
                    >
                      Amount
                    </label>
                    <Input
                      id="feeAmount"
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      {...register('feeAmount', { valueAsNumber: true })}
                      onBlur={() => {
                        trigger('feeAmount');
                        const val = watch('feeAmount');
                        if (val === 0 || val == null || isNaN(val)) {
                          setCustomErrors((prev) => ({
                            ...prev,
                            feeAmount: `VAL-INVALID-AMT: ${LEGACY_ERROR_CODES['VAL-INVALID-AMT']}`,
                          }));
                        } else {
                          setCustomErrors((prev) => {
                            const next = { ...prev };
                            delete next.feeAmount;
                            return next;
                          });
                        }
                      }}
                      aria-invalid={!!fieldError('feeAmount')}
                    />
                    <FieldError message={fieldError('feeAmount')} />
                  </div>
                )}

                {/* Currency */}
                <div>
                  <label
                    htmlFor="currency"
                    className="block text-sm font-medium mb-1"
                  >
                    Currency
                  </label>
                  <Input
                    id="currency"
                    placeholder="USD"
                    maxLength={3}
                    {...register('currency')}
                    onBlur={() => trigger('currency')}
                    aria-invalid={!!fieldError('currency')}
                  />
                  <FieldError message={fieldError('currency')} />
                </div>

                {/* Date */}
                <div>
                  <label
                    htmlFor="transactionDate"
                    className="block text-sm font-medium mb-1"
                  >
                    Transaction Date
                  </label>
                  <Input
                    id="transactionDate"
                    type="date"
                    max={getTodayString()}
                    {...register('transactionDate')}
                    onBlur={() => trigger('transactionDate')}
                    aria-invalid={!!fieldError('transactionDate')}
                  />
                  <FieldError message={fieldError('transactionDate')} />
                </div>

                {/* Description — FEE only */}
                {isFee && (
                  <div>
                    <label
                      htmlFor="description"
                      className="block text-sm font-medium mb-1"
                    >
                      Description
                    </label>
                    <Input
                      id="description"
                      placeholder="Fee description"
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
        isOpen={confirmOpen}
        transaction={pendingTransactionData}
        onConfirm={handleConfirm}
        onCancel={handleCancelConfirm}
      />
    </div>
  );
}

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return <p className="text-sm text-destructive mt-1">{message}</p>;
}
