import React, { useState, useEffect, useRef } from 'react';
import { KeyRound, ShieldAlert, AlertCircle, Info, Loader2, ArrowRight } from 'lucide-react';
import { api, ApiError } from '../services/api';
import type { Actor } from '../types';

interface AuthModalProps {
  isOpen: boolean;
  onSuccess: (token: string, actor: Actor) => void;
  onClose?: () => void;
  initialError?: string | null;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onSuccess,
  onClose,
  initialError,
}) => {
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(initialError || null);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);

  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);
  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanToken = token.trim();
    if (!cleanToken) {
      setError('Please provide an analyst bearer token.');
      return;
    }

    setLoading(true);
    setError(null);
    setErrorStatus(null);

    try {
      // Authenticate token against backend /v1/auth/me
      const actor = await api.getMe(cleanToken);

      if (!mounted.current) return;
      // Verify that actor has analyst role for case queue access
      if (actor.role !== 'analyst') {
        setError(
          `Forbidden: Token authenticates as role '${actor.role}' (${actor.identity}), but only 'analyst' credentials can access this console.`
        );
        setErrorStatus(403);
        setLoading(false);
        return;
      }

      onSuccess(cleanToken, actor);
      setToken('');
    } catch (err) {
      if (!mounted.current) return;
      if (err instanceof ApiError) {
        setErrorStatus(err.status);
        if (err.status === 401) {
          setError('401 Unauthorized: Invalid analyst bearer token. Ensure the secret is at least 24 characters and matches configured analyst keys.');
        } else if (err.status === 403) {
          setError(`403 Forbidden: ${err.detail}`);
        } else {
          setError(err.detail);
        }
      } else {
        setError('Failed to contact FraudShield backend. Check server connection.');
      }
    } finally {
      if (mounted.current) setLoading(false);
    }
  };

  return (
    <div role="dialog" aria-modal="true" aria-label="AuthModal" className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl max-w-md w-full overflow-hidden">
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-800 bg-slate-900/60 flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
            <KeyRound className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-100">Analyst Authentication</h2>
            <p className="text-xs text-slate-400">In-memory credential verification</p>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="analyst-token-input" className="block text-xs font-medium text-slate-300">
              Analyst Bearer Token <span className="text-rose-400">*</span>
            </label>
            <input
              id="analyst-token-input"
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Paste analyst token (min 24 characters)"
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent font-mono"
              autoFocus
              disabled={loading}
            />
          </div>

          {/* In-Memory Notice */}
          <div className="flex items-start gap-2 p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-xs text-slate-400">
            <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
            <div>
              <p className="text-slate-300 font-medium">Memory-Only Security Contract:</p>
              <p>Tokens remain in client memory only and are never saved to localStorage, sessionStorage, or client cookies.</p>
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div
              className={`p-3.5 rounded-lg border flex items-start gap-2.5 text-xs ${
                errorStatus === 403
                  ? 'bg-amber-950/40 border-amber-800/80 text-amber-300'
                  : 'bg-rose-950/40 border-rose-800/80 text-rose-300'
              }`}
            >
              {errorStatus === 403 ? (
                <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              )}
              <div className="leading-relaxed">{error}</div>
            </div>
          )}

          {/* Development / Demo Hint */}
          <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400">
            <div className="flex items-center justify-between">
              <span>Configured Analyst Identities:</span>
              <span className="font-mono text-slate-400">analyst_jane, analyst_bob</span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-2.5 pt-2">
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                disabled={loading}
                className="px-4 py-2 text-xs font-medium rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
              >
                Cancel
              </button>
            )}
            <button
              id="btn-analyst-signin"
              type="submit"
              disabled={loading || !token.trim()}
              className="flex items-center gap-2 px-4 py-2.5 text-xs font-medium rounded-lg text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm shadow-indigo-600/30 transition"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Verifying Token...</span>
                </>
              ) : (
                <>
                  <span>Authenticate Session</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
