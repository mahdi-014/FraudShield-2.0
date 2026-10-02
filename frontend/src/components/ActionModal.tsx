import React, { useState } from 'react';
import type { ReviewCase } from '../types';
import { api, ApiError } from '../services/api';
import { AlertCircle, Check, X, Loader2, AlertTriangle } from 'lucide-react';

interface ActionModalProps {
  isOpen: boolean;
  action: 'release' | 'reject';
  caseItem: ReviewCase;
  token: string;
  onSuccess: (updatedCase: ReviewCase) => void;
  onConflict: () => void;
  onClose: () => void;
}

export const ActionModal: React.FC<ActionModalProps> = ({
  isOpen,
  action,
  caseItem,
  token,
  onSuccess,
  onConflict,
  onClose,
}) => {
  const [reason, setReason] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConflict, setIsConflict] = useState(false);

  if (!isOpen) return null;

  const tx = caseItem.transaction;
  const isRelease = action === 'release';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanReason = reason.trim();
    if (cleanReason.length < 3) {
      setError('Please provide a decision rationale of at least 3 characters.');
      return;
    }

    setSubmitting(true);
    setError(null);
    setIsConflict(false);

    try {
      const response = await api.executeAction(token, caseItem.id, {
        action,
        reason: cleanReason,
        expected_version: tx?.version ?? 1,
      });

      onSuccess(response.case);
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 409) {
          setIsConflict(true);
          setError(
            'Version / State Conflict (HTTP 409): This case or transaction was modified by another analyst or process. Please inspect the updated case state before taking further action.'
          );
          // Trigger queue and case refresh on conflict
          onConflict();
        } else {
          setError(err.detail);
        }
      } else {
        setError('Failed to execute decision. Verify backend connectivity.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl max-w-lg w-full overflow-hidden">
        {/* Header */}
        <div
          className={`px-6 py-5 border-b flex items-center gap-3 ${
            isRelease
              ? 'bg-emerald-950/40 border-emerald-800/40 text-emerald-200'
              : 'bg-rose-950/40 border-rose-800/40 text-rose-200'
          }`}
        >
          <div
            className={`w-10 h-10 rounded-lg flex items-center justify-center border ${
              isRelease
                ? 'bg-emerald-600/20 border-emerald-500/40 text-emerald-400'
                : 'bg-rose-600/20 border-rose-500/40 text-rose-400'
            }`}
          >
            {isRelease ? <Check className="w-5 h-5" /> : <X className="w-5 h-5" />}
          </div>
          <div>
            <h2 className="text-base font-semibold">
              Confirm Decision: {isRelease ? 'Release Transaction' : 'Reject Transaction'}
            </h2>
            <p className="text-xs opacity-80">
              Target Ref: <span className="font-mono font-medium">{tx?.client_transaction_id || '—'}</span> (Case: {caseItem.id.slice(0, 8)}...)
            </p>
          </div>
        </div>

        {/* Body Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Target Meta / Version Protection */}
          <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-lg text-xs space-y-1.5">
            <div className="flex items-center justify-between text-slate-400">
              <span>Optimistic Concurrency Protection:</span>
              <span className="font-mono text-indigo-400 font-semibold">
                expected_version = {tx?.version ?? 1}
              </span>
            </div>
            <div className="flex items-center justify-between text-slate-400">
              <span>Current Simulated Status:</span>
              <span className="font-mono text-slate-200">{tx?.status}</span>
            </div>
            <div className="flex items-center justify-between text-slate-400">
              <span>Resulting Status after Decision:</span>
              <span className="font-mono font-semibold text-slate-200">
                {isRelease ? 'completed' : 'rejected'}
              </span>
            </div>
          </div>

          {/* Rationale Input */}
          <div className="space-y-1.5">
            <label htmlFor="action-reason-input" className="block text-xs font-medium text-slate-300">
              Analyst Decision Rationale <span className="text-rose-400">*</span>
            </label>
            <textarea
              id="action-reason-input"
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explicitly describe rationale (e.g. Simulated analyst decision: customer identity verified via simulated OTP and profile match)..."
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
              disabled={submitting || isConflict}
              autoFocus
            />
            <p className="text-[11px] text-slate-500">
              Minimum 3 characters. Any claimed customer verification must be stated as simulated.
            </p>
          </div>

          {/* Error Banner */}
          {error && (
            <div
              className={`p-3.5 rounded-lg border text-xs flex items-start gap-2.5 ${
                isConflict
                  ? 'bg-amber-950/40 border-amber-800/80 text-amber-300'
                  : 'bg-rose-950/40 border-rose-800/80 text-rose-300'
              }`}
            >
              {isConflict ? (
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              )}
              <div className="space-y-1">
                <p className="font-semibold">{isConflict ? 'Conflict Warning:' : 'Submission Error:'}</p>
                <p>{error}</p>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 text-xs font-medium rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
            >
              {isConflict ? 'Close & Review Current State' : 'Cancel'}
            </button>

            {!isConflict && (
              <button
                id="btn-confirm-action"
                type="submit"
                disabled={submitting || reason.trim().length < 3}
                className={`flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg text-white transition disabled:opacity-50 disabled:cursor-not-allowed shadow-sm ${
                  isRelease
                    ? 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/30'
                    : 'bg-rose-600 hover:bg-rose-500 shadow-rose-600/30'
                }`}
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Executing Decision...</span>
                  </>
                ) : (
                  <>
                    {isRelease ? <Check className="w-4 h-4" /> : <X className="w-4 h-4" />}
                    <span>Confirm {isRelease ? 'Release' : 'Reject'}</span>
                  </>
                )}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};
