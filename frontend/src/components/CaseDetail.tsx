import React, { useState } from 'react';
import type { ReviewCase } from '../types';
import { formatDhakaTime } from '../services/api';
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Layers,
  FileText,
  TrendingUp,
  TrendingDown,
  Info,
  Search,
  Check,
  X,
  History,
} from 'lucide-react';
import { AuditTimeline } from './AuditTimeline';

interface CaseDetailProps {
  caseItem: ReviewCase;
  analystToken: string;
  onOpenActionModal: (action: 'release' | 'reject') => void;
  auditRefreshTrigger: number;
}

export const CaseDetail: React.FC<CaseDetailProps> = ({
  caseItem,
  analystToken,
  onOpenActionModal,
  auditRefreshTrigger,
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'features' | 'audit'>('overview');
  const [featureSearch, setFeatureSearch] = useState('');

  const tx = caseItem.transaction;
  const isEligibleForAction =
    caseItem.status === 'open' &&
    (tx?.status === 'held_for_review' || tx?.status === 'pending_verification');

  const rawFeatures = tx?.features || {};
  const featureEntries = Object.entries(rawFeatures).filter(([k]) =>
    k.toLowerCase().includes(featureSearch.toLowerCase())
  );

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col h-full shadow-lg">
      {/* Top Header: Case & Transaction Meta */}
      <div className="p-5 border-b border-slate-800 bg-slate-900/90 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                Case Details
              </span>
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                ID: {caseItem.id.slice(0, 8)}...
              </span>
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-800/40">
                Tx Version: {tx?.version ?? 1}
              </span>
            </div>
            <h1 className="text-lg font-bold text-slate-100 font-mono tracking-tight mt-0.5">
              Client Ref: {tx?.client_transaction_id || '—'}
            </h1>
          </div>

          {/* Action Decision Controls */}
          <div className="flex items-center gap-2 shrink-0">
            {isEligibleForAction ? (
              <>
                <button
                  id="btn-case-release"
                  type="button"
                  onClick={() => onOpenActionModal('release')}
                  className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg text-emerald-100 bg-emerald-700 hover:bg-emerald-600 shadow-sm shadow-emerald-700/30 transition cursor-pointer"
                >
                  <Check className="w-4 h-4" />
                  <span>Release Transaction</span>
                </button>
                <button
                  id="btn-case-reject"
                  type="button"
                  onClick={() => onOpenActionModal('reject')}
                  className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg text-rose-100 bg-rose-700 hover:bg-rose-600 shadow-sm shadow-rose-700/30 transition cursor-pointer"
                >
                  <X className="w-4 h-4" />
                  <span>Reject Transaction</span>
                </button>
              </>
            ) : (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs">
                {caseItem.resolution === 'released' ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className="text-emerald-300 font-medium">Terminal State: Released</span>
                  </>
                ) : caseItem.resolution === 'rejected' ? (
                  <>
                    <XCircle className="w-4 h-4 text-rose-400" />
                    <span className="text-rose-300 font-medium">Terminal State: Rejected</span>
                  </>
                ) : (
                  <>
                    <ShieldAlert className="w-4 h-4 text-slate-400" />
                    <span className="text-slate-300 font-medium">Case Resolved ({caseItem.status})</span>
                  </>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Resolution details if already resolved */}
        {caseItem.status === 'resolved' && (
          <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg text-xs space-y-1">
            <div className="flex flex-wrap items-center justify-between text-slate-400 gap-2">
              <div>
                Resolved by: <span className="font-mono text-slate-200">{caseItem.resolved_by || 'analyst'}</span>
              </div>
              <div>
                Resolved at: <span className="text-slate-300">{formatDhakaTime(caseItem.resolved_at)}</span>
              </div>
            </div>
            {caseItem.resolution_reason && (
              <p className="text-slate-300 italic pt-1 border-t border-slate-800/60">
                "{caseItem.resolution_reason}"
              </p>
            )}
          </div>
        )}

        {/* Tabs */}
        <div className="flex items-center gap-1 border-b border-slate-800/80 pt-1 -mb-3">
          <button
            type="button"
            onClick={() => setActiveTab('overview')}
            className={`px-3 py-2 text-xs font-medium border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'overview'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Overview & TreeSHAP</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('features')}
            className={`px-3 py-2 text-xs font-medium border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'features'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Saved Feature Snapshot ({Object.keys(rawFeatures).length})</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('audit')}
            className={`px-3 py-2 text-xs font-medium border-b-2 transition flex items-center gap-1.5 ${
              activeTab === 'audit'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Audit Trail</span>
          </button>
        </div>
      </div>

      {/* Main Tab Content */}
      <div className="flex-1 overflow-y-auto p-5">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Cards Grid: Uncalibrated Score + Action + Status */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {/* Uncalibrated Score Card */}
              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Uncalibrated Model Score
                    </span>
                    <span title="Uncalibrated score under class weighting">
                      <Info className="w-3.5 h-3.5 text-slate-400" />
                    </span>
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-3xl font-bold font-mono text-slate-100">
                      {tx?.model_score !== undefined ? tx.model_score.toFixed(4) : '—'}
                    </span>
                    <span className="text-xs text-slate-400">/ 1.0000</span>
                  </div>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-800/80 text-[11px] text-amber-300/90 leading-tight">
                  Uncalibrated model score, not validated fraud probability. Class weighting and margin transformations apply.
                </div>
              </div>

              {/* Recommended Action Card */}
              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl flex flex-col justify-between">
                <div>
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Recommended Policy Action
                  </span>
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-xl font-bold uppercase tracking-wide text-slate-100">
                      {tx?.recommended_action || '—'}
                    </span>
                    {tx?.recommended_action === 'hold' && (
                      <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
                    )}
                  </div>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
                  Threshold Action: {tx?.recommended_action?.toUpperCase()}
                </div>
              </div>

              {/* Simulated Transaction Status Card */}
              <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl flex flex-col justify-between">
                <div>
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Simulated Payment Status
                  </span>
                  <div className="mt-2 text-sm font-semibold font-mono text-indigo-300">
                    {tx?.status || '—'}
                  </div>
                </div>
                <div className="mt-3 pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
                  Version: v{tx?.version} • Created: {formatDhakaTime(tx?.created_at)}
                </div>
              </div>
            </div>

            {/* Policy Reasons & Version Metadata */}
            <div className="p-4 bg-slate-950/50 border border-slate-800 rounded-xl space-y-3">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <FileText className="w-3.5 h-3.5 text-indigo-400" />
                <span>Policy Evaluation & System Versions</span>
              </h3>

              <div className="space-y-1.5">
                {tx?.policy_reasons && tx.policy_reasons.length > 0 ? (
                  tx.policy_reasons.map((reason, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 flex items-start gap-2"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                      <span>{reason}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-400">No explicit policy reasons recorded.</p>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 border-t border-slate-800 text-[11px] text-slate-400 font-mono">
                <div>
                  Model: <span className="text-slate-300">{tx?.model_version}</span>
                </div>
                <div>
                  Policy: <span className="text-slate-300">{tx?.policy_version}</span>
                </div>
                <div>
                  Schema: <span className="text-slate-300">{tx?.schema_version}</span>
                </div>
              </div>
            </div>

            {/* TreeSHAP Feature Factors */}
            <div className="p-4 bg-slate-950/50 border border-slate-800 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <TrendingUp className="w-3.5 h-3.5 text-indigo-400" />
                  <span>TreeSHAP Feature Explanations (Log-Odds Contributions)</span>
                </h3>
                <span className="text-[11px] text-slate-400 font-mono">
                  Units: log odds
                </span>
              </div>

              <div className="p-2.5 bg-amber-500/10 border border-amber-500/20 rounded-lg text-xs text-amber-300 flex items-start gap-2">
                <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                <span>
                  <strong>Statistical Association Notice:</strong> Top factors represent model associations within the historical dataset, not causal proof or exhaustive explanations.
                </span>
              </div>

              {tx?.model_factors && tx.model_factors.length > 0 ? (
                <div className="space-y-2 pt-1">
                  {tx.model_factors.map((factor, index) => {
                    const isIncrease = factor.direction === 'increases_score';
                    const absVal = Math.abs(factor.contribution_log_odds);
                    const widthPercent = Math.min(100, Math.max(10, absVal * 45));

                    return (
                      <div
                        key={index}
                        className="p-3 bg-slate-900 border border-slate-800 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
                      >
                        <div className="space-y-1 min-w-[180px]">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-semibold text-slate-200">
                              {factor.feature}
                            </span>
                            <span
                              className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium ${
                                isIncrease
                                  ? 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
                                  : 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                              }`}
                            >
                              {isIncrease ? (
                                <TrendingUp className="w-2.5 h-2.5 text-rose-400" />
                              ) : (
                                <TrendingDown className="w-2.5 h-2.5 text-emerald-400" />
                              )}
                              {isIncrease ? 'Increases Score' : 'Decreases Score'}
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-400 font-mono">
                            Feature Value: <span className="text-slate-300">{String(factor.value ?? 'null')}</span>
                          </div>
                        </div>

                        {/* Bar representation & log-odds number */}
                        <div className="flex items-center gap-3 w-full sm:w-60 shrink-0">
                          <div className="flex-1 bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
                            <div
                              className={`h-full rounded-full ${
                                isIncrease ? 'bg-rose-500' : 'bg-emerald-500'
                              }`}
                              style={{ width: `${widthPercent}%` }}
                            />
                          </div>
                          <span className="font-mono font-bold text-slate-200 text-right w-16">
                            {factor.contribution_log_odds >= 0 ? '+' : ''}
                            {factor.contribution_log_odds.toFixed(4)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-xs text-slate-400">No feature factors generated for this transaction.</p>
              )}
            </div>
          </div>
        )}

        {/* Feature Snapshot Tab */}
        {activeTab === 'features' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-4">
              <div className="relative flex-1 max-w-sm">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
                <input
                  type="text"
                  placeholder="Filter feature names (e.g. card, addr, dist)..."
                  value={featureSearch}
                  onChange={(e) => setFeatureSearch(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <span className="text-xs text-slate-400 font-mono">
                {featureEntries.length} of {Object.keys(rawFeatures).length} features
              </span>
            </div>

            <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 bg-slate-900/80 text-slate-400">
                    <th className="py-2.5 px-4 font-semibold uppercase tracking-wider w-1/3">Feature Name</th>
                    <th className="py-2.5 px-4 font-semibold uppercase tracking-wider">Saved Value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {featureEntries.length === 0 ? (
                    <tr>
                      <td colSpan={2} className="py-8 text-center text-slate-500">
                        No features matching "{featureSearch}"
                      </td>
                    </tr>
                  ) : (
                    featureEntries.map(([key, val]) => (
                      <tr key={key} className="hover:bg-slate-900/40 transition">
                        <td className="py-2 px-4 text-slate-300 font-medium">{key}</td>
                        <td className="py-2 px-4 text-slate-400">
                          {val === null ? (
                            <span className="text-slate-600 italic">null</span>
                          ) : typeof val === 'number' ? (
                            <span className="text-indigo-300 font-semibold">{val}</span>
                          ) : (
                            <span className="text-slate-200">"{String(val)}"</span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Audit Trail Tab */}
        {activeTab === 'audit' && (
          <AuditTimeline
            key={caseItem.transaction_id}
            transactionId={caseItem.transaction_id}
            token={analystToken}
            refreshTrigger={auditRefreshTrigger}
          />
        )}
      </div>
    </div>
  );
};
