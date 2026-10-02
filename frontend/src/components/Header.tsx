import React from 'react';
import type { Actor, HealthResponse } from '../types';
import { ShieldCheck, Wifi, WifiOff, LogOut, Lock, UserCheck, AlertTriangle } from 'lucide-react';

interface HeaderProps {
  actor: Actor | null;
  health: HealthResponse | null;
  healthLoading: boolean;
  onSignOut: () => void;
  onOpenSignIn: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  actor,
  health,
  healthLoading,
  onSignOut,
  onOpenSignIn,
}) => {
  const isConnected = health?.status === 'ready' && health?.database === 'connected';

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-30">
      {/* Top Banner Notice */}
      <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-1.5 text-xs text-amber-300 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span>
            <strong className="font-semibold">Simulated Transactions Notice:</strong> Research prototype operating on historical replay. No real-world funds move; customer OTP verification and acknowledgement flows are simulated.
          </span>
        </div>
        <span className="hidden md:inline text-amber-400/80 font-mono text-[11px]">
          Target rails: Historical Replay
        </span>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400 shadow-sm shadow-indigo-500/10">
            <ShieldCheck className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg text-slate-100 tracking-tight">FraudShield</span>
              <span className="text-[11px] font-medium uppercase px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300">
                Milestone 3
              </span>
            </div>
            <p className="text-xs text-slate-400">Analyst Risk & Decision Console</p>
          </div>
        </div>

        {/* Right side controls: Health + Auth */}
        <div className="flex items-center gap-4">
          {/* Backend Connection Status */}
          <div
            className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border ${
              healthLoading
                ? 'bg-slate-800 border-slate-700 text-slate-400'
                : isConnected
                ? 'bg-emerald-950/60 border-emerald-800/80 text-emerald-300'
                : 'bg-rose-950/60 border-rose-800/80 text-rose-300'
            }`}
            title={
              isConnected
                ? 'Backend connected and PostgreSQL healthy'
                : 'Backend or database is offline'
            }
          >
            {isConnected ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <Wifi className="w-3.5 h-3.5 text-emerald-400" />
                <span className="hidden sm:inline">DB Connected</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-rose-400" />
                <WifiOff className="w-3.5 h-3.5 text-rose-400" />
                <span className="hidden sm:inline">API Disconnected</span>
              </>
            )}
          </div>

          {/* Authentication State */}
          {actor ? (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/80 border border-slate-700/80 rounded-lg text-xs">
                <UserCheck className="w-4 h-4 text-emerald-400" />
                <div className="text-left">
                  <div className="font-medium text-slate-200">{actor.identity}</div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider">{actor.role}</div>
                </div>
              </div>
              <button
                type="button"
                onClick={onSignOut}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 transition"
                title="Sign out and purge in-memory credential"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Sign Out</span>
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={onOpenSignIn}
              className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium rounded-lg text-white bg-indigo-600 hover:bg-indigo-500 shadow-sm shadow-indigo-600/30 transition"
            >
              <Lock className="w-3.5 h-3.5" />
              <span>Analyst Sign In</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
