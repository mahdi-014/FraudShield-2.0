'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Header from '@/components/Header';
import { Eye, AlertTriangle, Search } from 'lucide-react';

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [filter, setFilter] = useState('ALL');
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/transactions?limit=50')
      .then((res) => res.json())
      .then((data) => setTransactions(data))
      .catch((err) => {
        console.log('Using synthetic mock transaction feed:', err);
        // Fallback demo transaction data
        setTransactions([
          {
            id: '1',
            transaction_id: 'TX10021',
            user_id: 'USR_1001',
            account_id: 'ACC_2001',
            amount: 7850.00,
            currency: 'USD',
            transaction_type: 'WIRE',
            device_id: 'DEV_RING_999',
            timestamp: new Date().toISOString(),
            fused_risk_score: 0.94,
            risk_level: 'CRITICAL',
          },
          {
            id: '2',
            transaction_id: 'TX10022',
            user_id: 'USR_1002',
            account_id: 'ACC_2002',
            amount: 3200.00,
            currency: 'USD',
            transaction_type: 'P2P',
            device_id: 'DEV_NEW_401',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            fused_risk_score: 0.68,
            risk_level: 'HIGH',
          },
          {
            id: '3',
            transaction_id: 'TX10023',
            user_id: 'USR_1003',
            account_id: 'ACC_2003',
            amount: 145.50,
            currency: 'USD',
            transaction_type: 'CARD',
            device_id: 'DEV_100',
            timestamp: new Date(Date.now() - 7200000).toISOString(),
            fused_risk_score: 0.12,
            risk_level: 'LOW',
          },
          {
            id: '4',
            transaction_id: 'TX10024',
            user_id: 'USR_1004',
            account_id: 'ACC_2004',
            amount: 4900.00,
            currency: 'USD',
            transaction_type: 'CARD',
            device_id: 'DEV_UPGRADE_301',
            timestamp: new Date(Date.now() - 10800000).toISOString(),
            fused_risk_score: 0.45,
            risk_level: 'MEDIUM',
          },
        ]);
      });
  }, []);

  const filtered = transactions.filter((t) => {
    if (filter !== 'ALL' && t.risk_level !== filter) return false;
    if (search && !t.transaction_id.toLowerCase().includes(search.toLowerCase()) && !t.user_id.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const getBadgeClass = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'HIGH':
        return 'bg-orange-500/10 text-orange-400 border-orange-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      default:
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
    }
  };

  return (
    <div className="flex-1 pb-12">
      <Header title="Live Transactions Stream" subtitle="Continuous Risk Ingestion & Behavior Profiling" />

      <main className="px-8 py-6 max-w-7xl mx-auto space-y-6">
        {/* Controls */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="flex items-center space-x-2 text-xs">
            <span className="text-slate-400 font-medium mr-2">Filter Risk Level:</span>
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setFilter(lvl)}
                className={`px-3 py-1.5 rounded-lg border font-mono transition-colors ${
                  filter === lvl
                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 font-bold'
                    : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>

          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search TX ID or User..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 rounded-lg pl-9 pr-4 py-2 w-full focus:outline-none focus:border-emerald-500/50"
            />
          </div>
        </div>

        {/* Transactions Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-slate-400 uppercase font-mono border-b border-slate-800">
                <tr>
                  <th className="p-4">Transaction ID</th>
                  <th className="p-4">User & Account</th>
                  <th className="p-4">Amount</th>
                  <th className="p-4">Type</th>
                  <th className="p-4">Device ID</th>
                  <th className="p-4">Timestamp</th>
                  <th className="p-4">Risk Score</th>
                  <th className="p-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filtered.map((tx) => (
                  <tr key={tx.transaction_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-4 font-mono font-bold text-slate-100 flex items-center space-x-2">
                      <span>{tx.transaction_id}</span>
                      {tx.risk_level === 'CRITICAL' && <AlertTriangle className="w-3.5 h-3.5 text-rose-400 animate-pulse" />}
                    </td>
                    <td className="p-4">
                      <p className="font-semibold text-slate-200">{tx.user_id}</p>
                      <p className="text-[10px] text-slate-500">{tx.account_id}</p>
                    </td>
                    <td className="p-4 font-mono font-semibold text-slate-100">
                      ${tx.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="p-4">
                      <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 font-mono text-[10px]">
                        {tx.transaction_type}
                      </span>
                    </td>
                    <td className="p-4 font-mono text-slate-400 text-[11px]">{tx.device_id || 'N/A'}</td>
                    <td className="p-4 text-slate-400 text-[11px]">
                      {new Date(tx.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="p-4">
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-0.5 rounded border text-[10px] font-bold font-mono ${getBadgeClass(tx.risk_level)}`}>
                          {tx.risk_level} ({(tx.fused_risk_score * 100).toFixed(0)}%)
                        </span>
                      </div>
                    </td>
                    <td className="p-4 text-right">
                      <Link
                        href={`/transactions/${tx.transaction_id}`}
                        className="inline-flex items-center space-x-1 px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded-lg border border-emerald-500/30 text-xs font-medium transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Investigate</span>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
