import React, { useState, useEffect, useCallback, useRef } from 'react';
import type { AuditEvent } from '../types';
import { api, formatDhakaTime } from '../services/api';
import { History, UserCheck, Server, ArrowRight, Clock, AlertCircle, RotateCw } from 'lucide-react';

interface AuditTimelineProps {
  transactionId: string;
  token: string;
  refreshTrigger: number;
}

export const AuditTimeline: React.FC<AuditTimelineProps> = ({
  transactionId,
  token,
  refreshTrigger,
}) => {
  const controller = useRef<AbortController | null>(null);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAudit = useCallback(async () => {
    if (!transactionId || !token) return;
    controller.current?.abort();
    const request = new AbortController();
    controller.current = request;
    setLoading(true);
    setError(null);
    try {
      const res = await api.getTransactionAudit(token, transactionId, request.signal);
      if (request.signal.aborted) return;
      setEvents(res.audit_events || []);
    } catch (err: unknown) {
      if (request.signal.aborted) return;
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to fetch audit log.');
      }
    } finally {
      if (!request.signal.aborted) setLoading(false);
    }
  }, [transactionId, token]);

  useEffect(() => {
    fetchAudit();
    return () => controller.current?.abort();
  }, [fetchAudit, refreshTrigger]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-indigo-400" />
          <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
            Audit History ({events.length} Events)
          </h3>
        </div>
        <button
          type="button"
          onClick={fetchAudit}
          disabled={loading}
          className="flex items-center gap-1.5 px-2.5 py-1 text-xs text-slate-400 hover:text-slate-200 bg-slate-950 border border-slate-800 rounded-lg transition"
        >
          <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/40 border border-rose-800/80 rounded-lg text-xs text-rose-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading && events.length === 0 ? (
        <div className="flex items-center justify-center p-8 text-slate-400 gap-2">
          <RotateCw className="w-5 h-5 animate-spin text-indigo-400" />
          <span className="text-xs">Loading audit events...</span>
        </div>
      ) : events.length === 0 ? (
        <div className="p-6 text-center text-slate-500 border border-slate-800/60 rounded-xl bg-slate-950/40 text-xs">
          No audit entries recorded for this transaction.
        </div>
      ) : (
        <div className="relative pl-6 border-l-2 border-slate-800 space-y-6 my-2">
          {events.map((ev, idx) => {
            const isAnalyst = ev.actor_role === 'analyst';

            return (
              <div key={ev.id || idx} className="relative group">
                {/* Node indicator */}
                <div
                  className={`absolute -left-[31px] top-1 w-4 h-4 rounded-full border-2 bg-slate-950 flex items-center justify-center ${
                    isAnalyst
                      ? 'border-indigo-400 shadow-sm shadow-indigo-500/40'
                      : 'border-slate-500'
                  }`}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      isAnalyst ? 'bg-indigo-400' : 'bg-slate-500'
                    }`}
                  />
                </div>

                {/* Event Card */}
                <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2.5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-slate-100">
                        {ev.event_type}
                      </span>
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider ${
                          isAnalyst
                            ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40'
                            : 'bg-slate-800 text-slate-300 border border-slate-700'
                        }`}
                      >
                        {isAnalyst ? (
                          <UserCheck className="w-3 h-3 text-indigo-400" />
                        ) : (
                          <Server className="w-3 h-3 text-slate-400" />
                        )}
                        {ev.actor} ({ev.actor_role})
                      </span>
                    </div>

                    <div className="flex items-center gap-1 text-[11px] text-slate-400 font-mono">
                      <Clock className="w-3 h-3 text-slate-400" />
                      <span>{formatDhakaTime(ev.created_at)}</span>
                    </div>
                  </div>

                  {/* Status Transition */}
                  <div className="flex items-center gap-2 text-xs text-slate-300 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800/80 font-mono">
                    <span className="text-slate-500">{ev.previous_status || 'null'}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                    <span className="font-bold text-slate-100">{ev.resulting_status}</span>
                    <span className="text-slate-500 text-[11px] ml-auto">action: {ev.action}</span>
                  </div>

                  {/* Reason text */}
                  {ev.reason && (
                    <p className="text-xs text-slate-300 leading-relaxed pl-1 border-l-2 border-slate-800">
                      {ev.reason}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
