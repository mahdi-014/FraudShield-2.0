'use client';

import React, { useEffect, useState } from 'react';
import Header from '@/components/Header';
import { Cpu, CheckCircle } from 'lucide-react';

export default function ModelsPage() {
  const [models, setModels] = useState<any[]>([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/models')
      .then((res) => res.json())
      .then((data) => setModels(data))
      .catch(() => {
        setModels([
          {
            id: '1',
            model_name: 'Supervised XGBoost Fraud Classifier',
            version: 'xgb-v1.0',
            algorithm: 'XGBoost Classifier',
            training_dataset: 'Synthetic Financial Transactions 2.0 (100k samples)',
            threshold: 0.75,
            status: 'ACTIVE',
            created_by: 'system_ml_pipeline',
            created_at: new Date().toISOString(),
          },
          {
            id: '2',
            model_name: 'Isolation Forest Anomaly Model',
            version: 'iso-v1.0',
            algorithm: 'Isolation Forest',
            training_dataset: 'Baseline Normal Customer Profiles (95k samples)',
            threshold: 0.08,
            status: 'ACTIVE',
            created_by: 'system_ml_pipeline',
            created_at: new Date().toISOString(),
          },
        ]);
      });
  }, []);

  return (
    <div className="flex-1 pb-12">
      <Header title="Model Governance & Registry" subtitle="ML Model Version Control & Audit Governance" />

      <main className="px-8 py-6 max-w-7xl mx-auto space-y-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <Cpu className="w-5 h-5 text-cyan-400" />
              <h2 className="text-base font-bold text-slate-100">Registered Fraud Classifiers</h2>
            </div>
            <span className="text-xs text-slate-400 font-mono">2 Active Production Models</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {models.map((m) => (
              <div key={m.version} className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-slate-100 text-sm">{m.version}</span>
                  <span className="px-2.5 py-1 rounded bg-emerald-500/20 text-emerald-400 font-mono font-bold text-xs border border-emerald-500/30 flex items-center space-x-1">
                    <CheckCircle className="w-3 h-3 text-emerald-400" />
                    <span>{m.status}</span>
                  </span>
                </div>

                <div className="space-y-1 text-xs">
                  <p className="font-bold text-slate-200">{m.model_name}</p>
                  <p className="text-slate-400">Algorithm: <span className="font-mono text-slate-300">{m.algorithm}</span></p>
                  <p className="text-slate-400">Dataset: <span className="text-slate-300">{m.training_dataset}</span></p>
                  <p className="text-slate-400">Decision Threshold: <span className="font-mono text-cyan-400 font-bold">{m.threshold}</span></p>
                </div>

                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 font-mono">
                  <span>Author: {m.created_by}</span>
                  <span>Registered: {new Date(m.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
