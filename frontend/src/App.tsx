import React, { useState, useEffect, useCallback } from 'react';
import type { Actor, ReviewCase, HealthResponse } from './types';
import { api, ApiError } from './services/api';
import { Header } from './components/Header';
import { CaseQueue } from './components/CaseQueue';
import { CaseDetail } from './components/CaseDetail';
import { AuthModal } from './components/AuthModal';
import { ActionModal } from './components/ActionModal';
import {
  Lock,
  AlertCircle,
  CheckCircle2,
  FolderOpen,
} from 'lucide-react';

export const App: React.FC = () => {
  // In-memory authentication: strictly in component state (never localStorage/cookies)
  const [token, setToken] = useState<string | null>(null);
  const [actor, setActor] = useState<Actor | null>(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  // System Health
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);

  // Cases Queue State
  const [cases, setCases] = useState<ReviewCase[]>([]);
  const [totalCases, setTotalCases] = useState(0);
  const [queueLoading, setQueueLoading] = useState(false);
  const [queueError, setQueueError] = useState<string | null>(null);

  // Pagination & Filters
  const [offset, setOffset] = useState(0);
  const limit = 10;
  const [statusFilter, setStatusFilter] = useState('all');
  const [resolutionFilter, setResolutionFilter] = useState('all');
  const [actionFilter, setActionFilter] = useState('all');

  // Selected Case & Action Modal
  const [selectedCase, setSelectedCase] = useState<ReviewCase | null>(null);
  const [activeAction, setActiveAction] = useState<'release' | 'reject' | null>(null);
  const [auditRefreshTrigger, setAuditRefreshTrigger] = useState(0);
  const [toastMessage, setToastMessage] = useState<{ type: 'success' | 'conflict' | 'error'; text: string } | null>(null);

  // Check health periodically or on mount
  const verifyHealth = useCallback(async () => {
    try {
      setHealthLoading(true);
      const res = await api.checkHealth();
      setHealth(res);
    } catch {
      setHealth({ status: 'offline', mode: 'historical_dataset_replay', database: 'disconnected' });
    } finally {
      setHealthLoading(false);
    }
  }, []);

  useEffect(() => {
    verifyHealth();
    const interval = setInterval(verifyHealth, 15000);
    return () => clearInterval(interval);
  }, [verifyHealth]);

  // Fetch Cases Queue
  const fetchQueue = useCallback(async () => {
    if (!token) return;

    setQueueLoading(true);
    setQueueError(null);

    try {
      const res = await api.getCases(token, {
        status: statusFilter,
        resolution: resolutionFilter,
        recommended_action: actionFilter,
        limit,
        offset,
      });

      setCases(res.items || []);
      setTotalCases(res.total || 0);

      // Preserve selection or select first
      if (res.items && res.items.length > 0) {
        setSelectedCase((prev) => {
          if (!prev) return res.items[0];
          const found = res.items.find((c) => c.id === prev.id);
          return found || res.items[0];
        });
      } else {
        setSelectedCase(null);
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 401 || err.status === 403) {
          setAuthError(err.detail);
          setToken(null);
          setActor(null);
          setIsAuthModalOpen(true);
        } else {
          setQueueError(err.detail);
        }
      } else {
        setQueueError('Failed to fetch cases from backend.');
      }
    } finally {
      setQueueLoading(false);
    }
  }, [token, statusFilter, resolutionFilter, actionFilter, limit, offset]);

  useEffect(() => {
    if (token) {
      fetchQueue();
    }
  }, [fetchQueue, token]);

  // Refresh single selected case
  const refreshSelectedCase = useCallback(async () => {
    if (!token || !selectedCase) return;
    try {
      const refreshed = await api.getCase(token, selectedCase.id);
      setSelectedCase(refreshed);
    } catch (err) {
      console.error('Failed to refresh case:', err);
    }
  }, [token, selectedCase]);

  // Auth Callbacks
  const handleAuthSuccess = (newToken: string, newActor: Actor) => {
    setToken(newToken);
    setActor(newActor);
    setIsAuthModalOpen(false);
    setAuthError(null);
    setOffset(0);
    setToastMessage({
      type: 'success',
      text: `Authenticated successfully as ${newActor.identity} (${newActor.role}).`,
    });
  };

  const handleSignOut = () => {
    setToken(null);
    setActor(null);
    setCases([]);
    setTotalCases(0);
    setSelectedCase(null);
    setActiveAction(null);
    setToastMessage({
      type: 'success',
      text: 'Signed out. In-memory credentials purged.',
    });
  };

  // Decision Execution Callbacks
  const handleActionSuccess = (updatedCase: ReviewCase) => {
    setSelectedCase(updatedCase);
    setAuditRefreshTrigger((prev) => prev + 1);
    fetchQueue();
    setToastMessage({
      type: 'success',
      text: `Decision executed successfully: Case resolved as ${updatedCase.resolution}.`,
    });
  };

  const handleActionConflict = () => {
    refreshSelectedCase();
    fetchQueue();
    setAuditRefreshTrigger((prev) => prev + 1);
    setToastMessage({
      type: 'conflict',
      text: 'Concurrency Conflict: Record state or version was updated. Refreshed with latest data.',
    });
  };

  // Toast Auto-dismiss
  useEffect(() => {
    if (toastMessage) {
      const t = setTimeout(() => setToastMessage(null), 6000);
      return () => clearTimeout(t);
    }
  }, [toastMessage]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans">
      {/* Top Header */}
      <Header
        actor={actor}
        health={health}
        healthLoading={healthLoading}
        onSignOut={handleSignOut}
        onOpenSignIn={() => {
          setAuthError(null);
          setIsAuthModalOpen(true);
        }}
      />

      {/* Toast Notification Banner */}
      {toastMessage && (
        <div
          className={`px-4 py-2.5 text-xs flex items-center justify-between border-b ${
            toastMessage.type === 'success'
              ? 'bg-emerald-950/80 border-emerald-800 text-emerald-200'
              : toastMessage.type === 'conflict'
              ? 'bg-amber-950/80 border-amber-800 text-amber-200'
              : 'bg-rose-950/80 border-rose-800 text-rose-200'
          }`}
        >
          <div className="max-w-7xl mx-auto flex items-center gap-2 w-full">
            {toastMessage.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
            )}
            <span>{toastMessage.text}</span>
          </div>
          <button
            type="button"
            onClick={() => setToastMessage(null)}
            className="text-slate-400 hover:text-slate-200 text-xs font-mono ml-4"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 flex flex-col">
        {!token ? (
          /* Sign-In Required Landing State */
          <div className="flex-1 flex items-center justify-center p-6">
            <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center space-y-5 shadow-2xl">
              <div className="w-14 h-14 rounded-2xl bg-indigo-600/10 border border-indigo-500/30 flex items-center justify-center mx-auto text-indigo-400">
                <Lock className="w-7 h-7" />
              </div>
              <div className="space-y-1.5">
                <h2 className="text-xl font-bold text-slate-100">Analyst Sign In Required</h2>
                <p className="text-xs text-slate-400">
                  Access to the review queue and decision execution requires authenticated analyst credentials.
                </p>
              </div>

              <div className="p-3.5 bg-slate-950 border border-slate-800/80 rounded-xl text-xs text-slate-400 text-left space-y-1">
                <div className="font-semibold text-slate-300">Security Model:</div>
                <p>• In-memory bearer credential storage only</p>
                <p>• Role-based server-side authorization enforcement</p>
                <p>• Optimistic concurrency locking on transitions</p>
              </div>

              <button
                id="btn-prompt-signin"
                type="button"
                onClick={() => {
                  setAuthError(null);
                  setIsAuthModalOpen(true);
                }}
                className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-indigo-600/20 transition flex items-center justify-center gap-2"
              >
                <Lock className="w-4 h-4" />
                <span>Enter Analyst Bearer Token</span>
              </button>
            </div>
          </div>
        ) : queueError ? (
          /* Queue Error State */
          <div className="flex-1 flex items-center justify-center p-6">
            <div className="max-w-md w-full bg-slate-900 border border-rose-900/60 rounded-xl p-6 text-center space-y-4">
              <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-slate-100">Failed to Load Review Queue</h3>
                <p className="text-xs text-rose-300">{queueError}</p>
              </div>
              <button
                type="button"
                onClick={fetchQueue}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg transition"
              >
                Retry Request
              </button>
            </div>
          </div>
        ) : (
          /* Active Split-Pane Dashboard */
          <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-5 min-h-[600px]">
            {/* Left Column: Paginated Queue (5 columns on desktop) */}
            <div className="lg:col-span-5 h-[650px] lg:h-auto flex flex-col">
              <CaseQueue
                cases={cases}
                total={totalCases}
                limit={limit}
                offset={offset}
                loading={queueLoading}
                selectedCaseId={selectedCase?.id || null}
                statusFilter={statusFilter}
                resolutionFilter={resolutionFilter}
                actionFilter={actionFilter}
                onSelectCase={(c) => setSelectedCase(c)}
                onRefresh={fetchQueue}
                onPageChange={(newOffset) => setOffset(newOffset)}
                onStatusFilterChange={(val) => {
                  setStatusFilter(val);
                  setOffset(0);
                }}
                onResolutionFilterChange={(val) => {
                  setResolutionFilter(val);
                  setOffset(0);
                }}
                onActionFilterChange={(val) => {
                  setActionFilter(val);
                  setOffset(0);
                }}
              />
            </div>

            {/* Right Column: Case Detail & Actions (7 columns on desktop) */}
            <div className="lg:col-span-7 h-[650px] lg:h-auto flex flex-col">
              {selectedCase ? (
                <CaseDetail
                  caseItem={selectedCase}
                  analystToken={token}
                  onOpenActionModal={(action) => setActiveAction(action)}
                  auditRefreshTrigger={auditRefreshTrigger}
                />
              ) : (
                <div className="flex-1 bg-slate-900 border border-slate-800 rounded-xl flex flex-col items-center justify-center p-8 text-center text-slate-500">
                  <FolderOpen className="w-12 h-12 text-slate-700 mb-2" />
                  <p className="text-sm font-medium text-slate-300">No Case Selected</p>
                  <p className="text-xs max-w-xs text-slate-500 mt-1">
                    Select a review case from the queue to inspect TreeSHAP explanations, feature snapshots, and perform decision actions.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Auth Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        initialError={authError}
        onSuccess={handleAuthSuccess}
        onClose={actor ? () => setIsAuthModalOpen(false) : undefined}
      />

      {/* Decision Action Modal */}
      {activeAction && selectedCase && token && (
        <ActionModal
          isOpen={true}
          action={activeAction}
          caseItem={selectedCase}
          token={token}
          onSuccess={handleActionSuccess}
          onConflict={handleActionConflict}
          onClose={() => setActiveAction(null)}
        />
      )}
    </div>
  );
};

export default App;
