import React from 'react';
import type { ReviewCase } from '../types';
import { formatDhakaTime } from '../services/api';
import {
  RotateCw,
  Clock,
  Filter,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  ShieldCheck,
  PauseCircle,
  AlertTriangle,
  FolderOpen,
  CheckCircle2,
  XCircle,
} from 'lucide-react';

interface CaseQueueProps {
  cases: ReviewCase[];
  total: number;
  limit: number;
  offset: number;
  loading: boolean;
  selectedCaseId: string | null;
  statusFilter: string;
  resolutionFilter: string;
  actionFilter: string;
  onSelectCase: (caseItem: ReviewCase) => void;
  onRefresh: () => void;
  onPageChange: (newOffset: number) => void;
  onStatusFilterChange: (val: string) => void;
  onResolutionFilterChange: (val: string) => void;
  onActionFilterChange: (val: string) => void;
}

export const CaseQueue: React.FC<CaseQueueProps> = ({
  cases,
  total,
  limit,
  offset,
  loading,
  selectedCaseId,
  statusFilter,
  resolutionFilter,
  actionFilter,
  onSelectCase,
  onRefresh,
  onPageChange,
  onStatusFilterChange,
  onResolutionFilterChange,
  onActionFilterChange,
}) => {
  const currentPage = Math.floor(offset / limit) + 1;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  const getActionBadge = (action?: string) => {
    switch (action) {
      case 'hold':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-rose-500/10 border border-rose-500/30 text-rose-300">
            <ShieldAlert className="w-3 h-3 text-rose-400" />
            HOLD
          </span>
        );
      case 'pause':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-amber-500/10 border border-amber-500/30 text-amber-300">
            <PauseCircle className="w-3 h-3 text-amber-400" />
            PAUSE
          </span>
        );
      case 'warn':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-yellow-500/10 border border-yellow-500/30 text-yellow-300">
            <AlertTriangle className="w-3 h-3 text-yellow-400" />
            WARN
          </span>
        );
      case 'allow':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
            ALLOW
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 border border-slate-700 text-slate-300">
            {action || 'UNKNOWN'}
          </span>
        );
    }
  };

  const getStatusBadge = (txStatus?: string) => {
    switch (txStatus) {
      case 'held_for_review':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-rose-950/40 text-rose-400 border border-rose-800/40">
            Held For Review
          </span>
        );
      case 'pending_verification':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-amber-950/40 text-amber-400 border border-amber-800/40">
            Pending Verification
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-950/40 text-emerald-400 border border-emerald-800/40">
            Completed (Released)
          </span>
        );
      case 'rejected':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-red-950/40 text-red-400 border border-red-800/40">
            Rejected
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-400 border border-slate-700">
            {txStatus || '—'}
          </span>
        );
    }
  };

  const getCaseStateBadge = (caseItem: ReviewCase) => {
    if (caseItem.status === 'open') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-blue-500/10 border border-blue-500/30 text-blue-300">
          <FolderOpen className="w-3 h-3 text-blue-400" />
          Open
        </span>
      );
    }
    if (caseItem.resolution === 'released') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          Resolved: Released
        </span>
      );
    }
    if (caseItem.resolution === 'rejected') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-red-500/10 border border-red-500/30 text-red-300">
          <XCircle className="w-3 h-3 text-red-400" />
          Resolved: Rejected
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-300">
        Resolved
      </span>
    );
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col h-full shadow-lg">
      {/* Header & Filter Toolbar */}
      <div className="p-4 border-b border-slate-800 bg-slate-900/80 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-slate-100 uppercase tracking-wider">
              Analyst Case Queue
            </h2>
            <span className="px-2 py-0.5 rounded-full text-xs font-mono bg-slate-800 text-slate-300 border border-slate-700">
              {total} Total
            </span>
          </div>

          <button
            type="button"
            onClick={onRefresh}
            disabled={loading}
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-lg text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 transition"
            title="Refresh queue"
          >
            <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        </div>

        {/* Filter Bar */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
          {/* Status Filter */}
          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5">
            <Filter className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <span className="text-slate-400">Case:</span>
            <select
              aria-label="Filter by case status"
              value={statusFilter}
              onChange={(e) => onStatusFilterChange(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none w-full font-medium cursor-pointer"
            >
              <option value="all" className="bg-slate-900">All Cases</option>
              <option value="open" className="bg-slate-900">Open</option>
              <option value="resolved" className="bg-slate-900">Resolved</option>
            </select>
          </div>

          {/* Resolution Filter */}
          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5">
            <span className="text-slate-400">Resolution:</span>
            <select
              aria-label="Filter by resolution"
              value={resolutionFilter}
              onChange={(e) => onResolutionFilterChange(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none w-full font-medium cursor-pointer"
            >
              <option value="all" className="bg-slate-900">All Resolutions</option>
              <option value="released" className="bg-slate-900">Released</option>
              <option value="rejected" className="bg-slate-900">Rejected</option>
            </select>
          </div>

          {/* Recommended Action Filter */}
          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5">
            <span className="text-slate-400">Action:</span>
            <select
              aria-label="Filter by recommended action"
              value={actionFilter}
              onChange={(e) => onActionFilterChange(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none w-full font-medium cursor-pointer"
            >
              <option value="all" className="bg-slate-900">All Actions</option>
              <option value="hold" className="bg-slate-900">Hold</option>
              <option value="pause" className="bg-slate-900">Pause</option>
              <option value="warn" className="bg-slate-900">Warn</option>
              <option value="allow" className="bg-slate-900">Allow</option>
            </select>
          </div>
        </div>
      </div>

      {/* Case Table / List */}
      <div className="flex-1 overflow-y-auto min-h-[300px]">
        {loading && cases.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-slate-400 gap-2">
            <RotateCw className="w-6 h-6 animate-spin text-indigo-400" />
            <p className="text-xs">Loading review cases...</p>
          </div>
        ) : cases.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-slate-400 gap-2 p-6 text-center">
            <FolderOpen className="w-8 h-8 text-slate-600" />
            <p className="text-sm font-medium text-slate-300">No review cases match filter</p>
            <p className="text-xs text-slate-500 max-w-xs">
              Try adjusting your filter options or submitting transactions requiring review.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {cases.map((item) => {
              const isSelected = item.id === selectedCaseId;
              const tx = item.transaction;

              return (
                <div
                  key={item.id}
                  onClick={() => onSelectCase(item)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onSelectCase(item);
                    }
                  }}
                  tabIndex={0}
                  role="button"
                  aria-pressed={isSelected}
                  className={`p-3.5 text-left transition cursor-pointer flex flex-col gap-2 ${
                    isSelected
                      ? 'bg-indigo-950/40 border-l-4 border-indigo-500 pl-3'
                      : 'hover:bg-slate-800/50'
                  }`}
                >
                  {/* Row 1: Client ID + Case Status */}
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-slate-200">
                        Ref: {tx?.client_transaction_id || '—'}
                      </span>
                      {getActionBadge(tx?.recommended_action)}
                    </div>
                    <div>{getCaseStateBadge(item)}</div>
                  </div>

                  {/* Row 2: Score + Transaction Status */}
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <div className="flex items-center gap-2">
                      <span>Score:</span>
                      <span className="font-mono font-bold text-slate-200 text-sm">
                        {tx?.model_score !== undefined ? tx.model_score.toFixed(4) : '—'}
                      </span>
                    </div>
                    <div>{getStatusBadge(tx?.status)}</div>
                  </div>

                  {/* Row 3: Timestamp */}
                  <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/50">
                    <div className="flex items-center gap-1 text-slate-400">
                      <Clock className="w-3 h-3 text-slate-400" />
                      <span>{formatDhakaTime(item.created_at)}</span>
                    </div>
                    <span className="font-mono text-[10px] text-slate-400">
                      v{tx?.version || 1}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Pagination Footer */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/90 flex items-center justify-between text-xs text-slate-400">
        <div>
          Showing {total === 0 ? 0 : offset + 1}–{Math.min(offset + limit, total)} of {total}
        </div>
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => onPageChange(Math.max(0, offset - limit))}
            disabled={offset === 0 || loading}
            className="p-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed border border-slate-700 transition"
            title="Previous Page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="font-mono px-2 py-0.5 rounded bg-slate-950 border border-slate-800">
            {currentPage} / {totalPages}
          </span>
          <button
            type="button"
            onClick={() => onPageChange(offset + limit)}
            disabled={offset + limit >= total || loading}
            className="p-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed border border-slate-700 transition"
            title="Next Page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
