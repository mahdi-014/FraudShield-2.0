'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Header from '@/components/Header';
import { Bell, AlertTriangle, ShieldAlert, Eye, CheckCircle2 } from 'lucide-react';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/fraud/alerts')
      .then((res) => res.json())
      .then((data) => setAlerts(data))
      .catch(() => {
        setAlerts([
          {
            id: '1',
            alert_id: 'ALT_9001',
            transaction_id: 'TX10021',
            risk_score: 0.94,
            risk_level: 'CRITICAL',
            status: 'NEW',
            trigger_reason: 'Coordinated fraud ring device sharing + 5.2x baseline amount deviation',
            created_at: new Date().toISOString(),
          },
          {
            id: '2',
            alert_id: 'ALT_9002',
            transaction_id: 'TX10022',
            risk_score: 0.68,
            risk_level: 'HIGH',
            status: 'NEW',
            trigger_reason: 'Account Takeover Pattern: New device + unusual geographic location + WIRE',
            created_at: new Date(Date.now() - 3600000).toISOString(),
          },
        ]);
      });
  }, []);

  return (
    <div className="flex-1 pb-12">
      <Header title="Fraud Alerts Triage" subtitle="Real-time High-Risk Trigger Queue" />

      <main className="px-8 py-6 max-w-7xl mx-auto space-y-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <Bell className="w-5 h-5 text-rose-400" />
              <h2 className="text-base font-bold text-slate-100">Active Alert Feed</h2>
            </div>
            <span className="text-xs text-slate-400 font-mono">{alerts.length} Pending Triage</span>
          </div>

          <div className="space-y-4">
            {alerts.map((alert) => (
              <div key={alert.alert_id} className="bg-slate-950 border border-slate-800 rounded-lg p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-3">
                    <span className="font-mono font-bold text-sm text-slate-100">{alert.alert_id}</span>
                    <span className="text-xs font-mono text-slate-400">({alert.transaction_id})</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                      alert.risk_level === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' : 'bg-orange-500/20 text-orange-400 border border-orange-500/40'
                    }`}>
                      {alert.risk_level} ({(alert.risk_score * 100).toFixed(0)}%)
                    </span>
                  </div>
                  <p className="text-xs text-slate-300">{alert.trigger_reason}</p>
                </div>

                <div className="flex items-center space-x-3">
                  <Link
                    href={`/transactions/${alert.transaction_id}`}
                    className="px-4 py-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded-lg border border-emerald-500/30 text-xs font-medium transition-colors flex items-center space-x-1.5"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Investigate</span>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
