'use client';

import React from 'react';
import Header from '@/components/Header';
import { Sliders, ShieldCheck } from 'lucide-react';

export default function GovernancePage() {
  const metrics = [
    { label: 'Precision', value: '94.2%', target: '>90.0%', status: 'HEALTHY' },
    { label: 'Recall', value: '91.5%', target: '>88.0%', status: 'HEALTHY' },
    { label: 'F1 Score', value: '92.8%', target: '>89.0%', status: 'HEALTHY' },
    { label: 'PR-AUC', value: '96.1%', target: '>92.0%', status: 'HEALTHY' },
    { label: 'False Positive Rate (FPR)', value: '1.2%', target: '<3.0%', status: 'HEALTHY' },
    { label: 'False Negative Rate (FNR)', value: '8.5%', target: '<10.0%', status: 'HEALTHY' },
    { label: 'Inference Latency', value: '14.5 ms', target: '<50.0 ms', status: 'HEALTHY' },
    { label: 'Feature Drift Index (PSI)', value: '0.02', target: '<0.10', status: 'STABLE' },
  ];

  return (
    <div className="flex-1 pb-12">
      <Header title="Governance & Drift Monitoring" subtitle="Production Model Performance & Operational Metrics Audit" />

      <main className="px-8 py-6 max-w-7xl mx-auto space-y-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <Sliders className="w-5 h-5 text-emerald-400" />
              <h2 className="text-base font-bold text-slate-100">Supervised Model Quality Metrics</h2>
            </div>
            <div className="flex items-center space-x-2 text-xs text-emerald-400 bg-emerald-950 px-3 py-1 rounded-lg border border-emerald-500/30">
              <ShieldCheck className="w-4 h-4" />
              <span>Model Drift: Zero Drift Detected</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {metrics.map((m) => (
              <div key={m.label} className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>{m.label}</span>
                  <span className="text-[10px] font-mono text-emerald-400 font-bold">{m.status}</span>
                </div>
                <p className="text-2xl font-extrabold text-slate-100 font-mono">{m.value}</p>
                <p className="text-[10px] text-slate-500 font-mono">Benchmark SLA: {m.target}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
