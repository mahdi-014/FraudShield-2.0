'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Header from '@/components/Header';
import { Briefcase, Eye, UserCheck, Clock, CheckCircle } from 'lucide-react';

export default function CasesPage() {
  const [cases, setCases] = useState<any[]>([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/cases')
      .then((res) => res.json())
      .then((data) => setCases(data))
      .catch(() => {
        setCases([
          {
            id: '1',
            case_id: 'CAS_1001',
            title: 'Suspicious WIRE Transfer - TX10021',
            status: 'UNDER_INVESTIGATION',
            priority: 'CRITICAL',
            summary: 'Coordinated fraud ring cluster sharing device DEV_RING_999.',
            created_at: new Date().toISOString(),
          },
          {
            id: '2',
            case_id: 'CAS_1002',
            title: 'ATO Pattern Verification - TX10022',
            status: 'NEW',
            priority: 'HIGH',
            summary: 'New device added 15 minutes prior to high amount transfer.',
            created_at: new Date(Date.now() - 3600000).toISOString(),
          },
        ]);
      });
  }, []);

  return (
    <div className="flex-1 pb-12">
      <Header title="Case Management & Triage" subtitle="Analyst Investigation Lifecycle & Audit Records" />

      <main className="px-8 py-6 max-w-7xl mx-auto space-y-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <Briefcase className="w-5 h-5 text-amber-400" />
              <h2 className="text-base font-bold text-slate-100">Investigative Cases</h2>
            </div>
          </div>

          <div className="space-y-4">
            {cases.map((c) => (
              <div key={c.case_id} className="bg-slate-950 border border-slate-800 rounded-lg p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-3">
                    <span className="font-mono font-bold text-sm text-slate-100">{c.case_id}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                      c.priority === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40' : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                    }`}>
                      {c.priority}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 font-mono text-[10px] text-slate-300">
                      {c.status}
                    </span>
                  </div>
                  <p className="text-xs font-semibold text-slate-200">{c.title}</p>
                  <p className="text-xs text-slate-400">{c.summary}</p>
                </div>

                <div className="flex items-center space-x-3">
                  <Link
                    href={`/transactions/${c.title.split('- ').pop() || 'TX10021'}`}
                    className="px-4 py-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded-lg border border-emerald-500/30 text-xs font-medium transition-colors flex items-center space-x-1.5"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>View Evidence</span>
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
