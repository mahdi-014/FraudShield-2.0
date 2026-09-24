'use client';

import React from 'react';
import { Search, ShieldCheck, RefreshCw } from 'lucide-react';

interface HeaderProps {
  title: string;
  subtitle?: string;
  onRefresh?: () => void;
}

export default function Header({ title, subtitle, onRefresh }: HeaderProps) {
  return (
    <header className="h-16 bg-slate-900/90 backdrop-blur border-b border-slate-800 px-6 flex items-center justify-between sticky top-0 z-20">
      <div>
        <h1 className="text-xl font-bold text-slate-100 tracking-tight">{title}</h1>
        {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
      </div>

      <div className="flex items-center space-x-4">
        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search TX, Account, User ID..."
            className="bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 rounded-lg pl-9 pr-4 py-2 w-64 focus:outline-none focus:border-emerald-500/50"
          />
        </div>

        {/* Refresh Action */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-2 bg-slate-800/80 hover:bg-slate-800 text-slate-300 hover:text-emerald-400 rounded-lg border border-slate-700 transition-colors flex items-center space-x-1.5 text-xs font-medium"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Sync</span>
          </button>
        )}

        {/* Mode & Live status */}
        <div className="flex items-center space-x-2 px-3 py-1.5 bg-emerald-950/40 border border-emerald-500/20 rounded-lg text-xs text-emerald-400 font-mono">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Real-time Risk Active</span>
        </div>
      </div>
    </header>
  );
}
