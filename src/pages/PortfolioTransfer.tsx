import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ROUTES } from '../types/routes';
import { Container, PageHeader, Card, Button, Alert } from '../components';
import { Input } from '../components/ui/input';
import {
  ApiError,
  fetchPortfolio,
  transferPositions,
  type TransferResponse,
} from '../services/api';
import type { PortfolioHolding } from '../types/account';

interface SelectedPosition {
  symbol: string;
  shares: string;
}

const ACCOUNT_PATTERN = /^\d{10}$/;

export default function PortfolioTransfer() {
  const [sourceAccount, setSourceAccount] = useState('');
  const [destinationAccount, setDestinationAccount] = useState('');
  const [holdings, setHoldings] = useState<PortfolioHolding[]>([]);
  const [selected, setSelected] = useState<Record<string, SelectedPosition>>({});
  const [isLoadingHoldings, setIsLoadingHoldings] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TransferResponse | null>(null);

  const validateAccount = (value: string): string | null => {
    if (!ACCOUNT_PATTERN.test(value)) {
      return 'Account number must be exactly 10 digits';
    }
    return null;
  };

  const handleLoadHoldings = async () => {
    setError(null);
    setResult(null);
    const sourceError = validateAccount(sourceAccount);
    if (sourceError) {
      setError(`Source account: ${sourceError}`);
      return;
    }

    setIsLoadingHoldings(true);
    try {
      const portfolio = await fetchPortfolio(sourceAccount);
      setHoldings(portfolio.holdings);
      setSelected({});
    } catch (err) {
      setHoldings([]);
      setSelected({});
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Unable to load holdings for the source account.');
      }
    } finally {
      setIsLoadingHoldings(false);
    }
  };

  const toggleSelected = (holding: PortfolioHolding) => {
    setSelected((prev) => {
      const next = { ...prev };
      if (next[holding.symbol]) {
        delete next[holding.symbol];
      } else {
        next[holding.symbol] = {
          symbol: holding.symbol,
          shares: String(holding.shares),
        };
      }
      return next;
    });
  };

  const updateShares = (symbol: string, shares: string) => {
    setSelected((prev) => {
      if (!prev[symbol]) {
        return prev;
      }
      return { ...prev, [symbol]: { ...prev[symbol], shares } };
    });
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setResult(null);

    const sourceError = validateAccount(sourceAccount);
    if (sourceError) {
      setError(`Source account: ${sourceError}`);
      return;
    }
    const destinationError = validateAccount(destinationAccount);
    if (destinationError) {
      setError(`Destination account: ${destinationError}`);
      return;
    }
    if (sourceAccount === destinationAccount) {
      setError('Source and destination accounts must be different.');
      return;
    }

    const selectedEntries = Object.values(selected);
    if (selectedEntries.length === 0) {
      setError('Select at least one position to transfer.');
      return;
    }

    const positions: { symbol: string; shares: number }[] = [];
    for (const entry of selectedEntries) {
      const sharesNum = Number(entry.shares);
      if (!Number.isFinite(sharesNum) || sharesNum <= 0) {
        setError(`Enter a positive share quantity for ${entry.symbol}.`);
        return;
      }
      const holding = holdings.find((h) => h.symbol === entry.symbol);
      if (holding && sharesNum > holding.shares) {
        setError(
          `Cannot transfer more than ${holding.shares} share(s) of ${entry.symbol}.`
        );
        return;
      }
      positions.push({ symbol: entry.symbol, shares: sharesNum });
    }

    setIsSubmitting(true);
    try {
      const response = await transferPositions({
        source_account: sourceAccount,
        destination_account: destinationAccount,
        positions,
      });
      setResult(response);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred while submitting the transfer.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setSourceAccount('');
    setDestinationAccount('');
    setHoldings([]);
    setSelected({});
    setError(null);
    setResult(null);
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
            title="Portfolio Transfer"
            subtitle="Transfer securities between accounts"
          />

          <main className="space-y-6 animate-slide-up">
            {error && (
              <Alert variant="destructive" role="alert" className="animate-fade-in">
                {error}
              </Alert>
            )}

            {result?.success && (
              <Alert className="animate-fade-in" role="status">
                <div className="space-y-1">
                  <p className="font-medium">Transfer submitted successfully.</p>
                  <p className="text-sm">{result.message}</p>
                  <p className="text-sm text-muted-foreground">
                    Transfer ID: <span className="font-mono">{result.transfer_id}</span>
                  </p>
                </div>
              </Alert>
            )}

            <Card hover className="animate-fade-in">
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <label htmlFor="sourceAccount" className="text-sm font-medium">
                      Source Account
                    </label>
                    <Input
                      id="sourceAccount"
                      type="text"
                      placeholder="10-digit source account"
                      maxLength={10}
                      value={sourceAccount}
                      onChange={(e) =>
                        setSourceAccount(e.target.value.replace(/[^0-9]/g, ''))
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <label htmlFor="destinationAccount" className="text-sm font-medium">
                      Destination Account
                    </label>
                    <Input
                      id="destinationAccount"
                      type="text"
                      placeholder="10-digit destination account"
                      maxLength={10}
                      value={destinationAccount}
                      onChange={(e) =>
                        setDestinationAccount(e.target.value.replace(/[^0-9]/g, ''))
                      }
                    />
                  </div>
                </div>

                <div className="flex flex-wrap gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleLoadHoldings}
                    disabled={isLoadingHoldings || !sourceAccount}
                  >
                    {isLoadingHoldings ? 'Loading holdings…' : 'Load source holdings'}
                  </Button>
                  {(holdings.length > 0 ||
                    sourceAccount ||
                    destinationAccount ||
                    result) && (
                    <Button type="button" variant="ghost" onClick={resetForm}>
                      Reset
                    </Button>
                  )}
                </div>

                {holdings.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">Select positions to transfer</h3>
                    <div className="grid gap-3">
                      {holdings.map((holding) => {
                        const isSelected = Boolean(selected[holding.symbol]);
                        return (
                          <div
                            key={holding.symbol}
                            className="flex flex-col gap-3 rounded-md border border-border p-4 md:flex-row md:items-center md:justify-between"
                          >
                            <label className="flex items-center gap-3">
                              <input
                                type="checkbox"
                                className="h-4 w-4"
                                checked={isSelected}
                                onChange={() => toggleSelected(holding)}
                                aria-label={`Transfer ${holding.symbol}`}
                              />
                              <span className="font-medium">{holding.symbol}</span>
                              <span className="text-sm text-muted-foreground">
                                {holding.name} · {holding.shares} share(s) available
                              </span>
                            </label>
                            <div className="flex items-center gap-2 md:max-w-[220px]">
                              <label
                                htmlFor={`shares-${holding.symbol}`}
                                className="text-sm text-muted-foreground"
                              >
                                Shares
                              </label>
                              <Input
                                id={`shares-${holding.symbol}`}
                                type="number"
                                min={1}
                                max={holding.shares}
                                step={1}
                                disabled={!isSelected}
                                value={selected[holding.symbol]?.shares ?? ''}
                                onChange={(e) =>
                                  updateShares(holding.symbol, e.target.value)
                                }
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                <div className="flex justify-end">
                  <Button
                    type="submit"
                    disabled={
                      isSubmitting ||
                      !sourceAccount ||
                      !destinationAccount ||
                      Object.keys(selected).length === 0
                    }
                  >
                    {isSubmitting ? 'Submitting…' : 'Submit transfer'}
                  </Button>
                </div>
              </form>
            </Card>
          </main>
        </div>
      </Container>
    </div>
  );
}
