import { useEffect, useRef } from 'react';
import type { EsgAuditEntry } from '../types/esg';
import { formatAsOfMonth, formatIntensity, formatTimestamp } from '../utils/esgFormat';
import { trapFocus } from '../utils/accessibility';

export interface EsgAuditHistoryProps {
  isOpen: boolean;
  entries: EsgAuditEntry[];
  loading?: boolean;
  error?: string | null;
  onClose: () => void;
}

export default function EsgAuditHistory({ isOpen, entries, loading = false, error = null, onClose }: EsgAuditHistoryProps) {
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const cleanup = dialogRef.current ? trapFocus(dialogRef.current) : undefined;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('keydown', handleEscape);
      cleanup?.();
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true" aria-labelledby="esg-history-title">
      <div ref={dialogRef} className="w-full max-w-2xl mx-4 rounded-xl border bg-card p-6 shadow-lg">
        <div className="flex items-start justify-between">
          <div>
            <h2 id="esg-history-title" className="text-lg font-semibold">Carbon intensity override history</h2>
            <p className="text-sm text-muted-foreground">Newest first. Entries are append-only and cannot be edited.</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 text-sm font-medium rounded-md border border-gray-300 bg-white hover:bg-gray-50"
          >
            Close
          </button>
        </div>

        <div className="mt-4 max-h-96 overflow-y-auto">
          {loading && <p className="text-sm text-muted-foreground" role="status">Loading history...</p>}
          {!loading && error && <p className="text-sm text-red-600" role="alert">{error}</p>}
          {!loading && !error && entries.length === 0 && (
            <p className="text-sm text-muted-foreground" data-testid="esg-history-empty">No overrides have been recorded for this portfolio.</p>
          )}
          {!loading && !error && entries.length > 0 && (
            <table className="w-full text-sm" data-testid="esg-history-table">
              <thead>
                <tr className="text-left text-muted-foreground border-b">
                  <th className="py-2 pr-3 font-medium">When</th>
                  <th className="py-2 pr-3 font-medium">Action</th>
                  <th className="py-2 pr-3 font-medium">Month</th>
                  <th className="py-2 pr-3 font-medium">Old</th>
                  <th className="py-2 pr-3 font-medium">New</th>
                  <th className="py-2 pr-3 font-medium">Who</th>
                  <th className="py-2 font-medium">Reason</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.id} className="border-b last:border-0 align-top">
                    <td className="py-2 pr-3 whitespace-nowrap">{formatTimestamp(entry.changed_at)}</td>
                    <td className="py-2 pr-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${entry.action === 'OVERRIDE' ? 'bg-amber-200 text-amber-900' : 'bg-emerald-200 text-emerald-900'}`}>
                        {entry.action === 'OVERRIDE' ? 'Override' : 'Clear'}
                      </span>
                    </td>
                    <td className="py-2 pr-3 whitespace-nowrap">{formatAsOfMonth(entry.as_of_month)}</td>
                    <td className="py-2 pr-3">{formatIntensity(entry.old_value)}</td>
                    <td className="py-2 pr-3">{formatIntensity(entry.new_value)}</td>
                    <td className="py-2 pr-3">{entry.changed_by}</td>
                    <td className="py-2">{entry.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
