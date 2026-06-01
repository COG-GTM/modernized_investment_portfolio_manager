import { useQuery } from '@tanstack/react-query';
import { fetchPortfolio, fetchTransactions } from '../services/api';

export function usePortfolioQuery(accountNumber: string | null) {
  return useQuery({
    queryKey: ['portfolio', accountNumber],
    queryFn: () => fetchPortfolio(accountNumber!),
    enabled: !!accountNumber,
  });
}

export function useTransactionsQuery(accountNumber: string | null) {
  return useQuery({
    queryKey: ['transactions', accountNumber],
    queryFn: () => fetchTransactions(accountNumber!),
    enabled: !!accountNumber,
  });
}
