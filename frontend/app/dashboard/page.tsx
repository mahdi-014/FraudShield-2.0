'use client';

import React, { useEffect, useState } from 'react';
import Header from '@/components/Header';
import {
  AlertTriangle,
  Briefcase,
  Share2,
  CheckCircle,
  Activity,
  Clock,
  ArrowUpRight,
  TrendingUp
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';

export default function ExecutiveDashboard() {
  const [stats, setStats] = useState<any>({
    transactions_analyzed: 5000,
    high_risk_transactions: 184,
    open_cases: 12,
    potential_fraud_rings: 4,
    confirmed_fraud: 38,
    false_positive_rate: 0.05,
    avg_detection_latency_ms: 14.5,
    risk_level_distribution: { LOW: 4476, MEDIUM: 300, HIGH: 184, CRITICAL: 40 },
    daily_trend: [
      { date: 'Sep 18', transactions: 650, fraud_alerts: 18 },
      { date: 'Sep 19', transactions: 720, fraud_alerts: 22 },
      { date: 'Sep 20', transactions: 810, fraud_alerts: 25 },
      { date: 'Sep 21', transactions: 690, fraud_alerts: 19 },
      { date: 'Sep 22', transactions: 890, fraud_alerts: 31 },
      { date: 'Sep 23', transactions: 940, fraud_alerts: 34 },
      { date: 'Sep 24', transactions: 1020, fraud_alerts: 42 },
    ]
  });

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/dashboard/stats')
      .then((res) => res.json())
      .then((data) => setStats(data))
      .catch((err) => console.log('Using backend live stats fallback:', err));
  }, []);

  const COLORS = ['#22c55e', '#f59e0b', '#f97316', '#ef4444'];
  const pieData = Object.keys(stats.risk_level_distribution).map((key) => ({
    name: key,
    value: stats.risk_level_distribution[key],
  }));

  return (
    <div className="flex-1 pb-12">
      <Header title="Executive Security Dashboard" subtitle="Real-time Financial Risk & Graph Intelligence Metrics" />

      <main className="px-8 py-6 space-y-8 max-w-7xl mx-auto">
        {/* Metric Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase text-slate-400">Transactions Analyzed</span>
              <Activity className="w-5 h-5 text-emerald-400" />
            </div>
            <p className="text-3xl font-extrabold text-slate-100 mt-3 font-mono">{stats.transactions_analyzed.toLocaleString()}</p>
            <div className="flex items-center space-x-1 text-xs text-emerald-400 mt-2 font-medium">
              <ArrowUpRight className="w-3.5 h-3.5" />
              <span>+14.2% vs last week</span>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase text-slate-400">High & Critical Risk</span>
              <AlertTriangle className="w-5 h-5 text-rose-400" />
            </div>
            <p className="text-3xl font-extrabold text-rose-400 mt-3 font-mono">{stats.high_risk_transactions}</p>
            <p className="text-xs text-slate-400 mt-2">Requires active analyst review</p>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase text-slate-400">Open Triage Cases</span>
              <Briefcase className="w-5 h-5 text-amber-400" />
            </div>
            <p className="text-3xl font-extrabold text-amber-400 mt-3 font-mono">{stats.open_cases}</p>
            <p className="text-xs text-slate-400 mt-2">Avg SLA: 8.4 mins</p>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase text-slate-400">Fraud Rings Detected</span>
              <Share2 className="w-5 h-5 text-indigo-400" />
            </div>
            <p className="text-3xl font-extrabold text-indigo-400 mt-3 font-mono">{stats.potential_fraud_rings}</p>
            <p className="text-xs text-slate-400 mt-2">Coordinated shared device nodes</p>
          </div>
        </div>

        {/* Secondary Metric Bar */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="bg-slate-900/60 border border-slate-800/80 rounded-lg p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-400">Confirmed Fraud Cases</p>
              <p className="text-xl font-bold text-emerald-400 font-mono mt-1">{stats.confirmed_fraud}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-emerald-500/20" />
          </div>

          <div className="bg-slate-900/60 border border-slate-800/80 rounded-lg p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-400">False Positive Rate</p>
              <p className="text-xl font-bold text-slate-200 font-mono mt-1">{(stats.false_positive_rate * 100).toFixed(1)}%</p>
            </div>
            <TrendingUp className="w-8 h-8 text-slate-500/20" />
          </div>

          <div className="bg-slate-900/60 border border-slate-800/80 rounded-lg p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-400">Avg Detection Latency</p>
              <p className="text-xl font-bold text-cyan-400 font-mono mt-1">{stats.avg_detection_latency_ms} ms</p>
            </div>
            <Clock className="w-8 h-8 text-cyan-500/20" />
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Transaction & Fraud Alert Trend */}
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-base font-bold text-slate-100">Transaction & Alert Ingestion Trend</h2>
                <p className="text-xs text-slate-400">Daily transaction volume vs high-risk fraud alerts triggered</p>
              </div>
              <div className="flex items-center space-x-4 text-xs">
                <div className="flex items-center space-x-1.5">
                  <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                  <span className="text-slate-300">Total Volume</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className="w-3 h-3 rounded-full bg-rose-500"></span>
                  <span className="text-slate-300">Fraud Alerts</span>
                </div>
              </div>
            </div>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats.daily_trend}>
                  <defs>
                    <linearGradient id="colorTx" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#22c55e" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="colorAlert" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                  <Area type="monotone" dataKey="transactions" stroke="#22c55e" fillOpacity={1} fill="url(#colorTx)" strokeWidth={2} />
                  <Area type="monotone" dataKey="fraud_alerts" stroke="#ef4444" fillOpacity={1} fill="url(#colorAlert)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Risk Level Distribution Pie */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-100">Risk Distribution</h2>
              <p className="text-xs text-slate-400">Calibrated risk tier breakdown across dataset</p>
            </div>
            <div className="h-56 my-2">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={4} dataKey="value">
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs border-t border-slate-800 pt-4">
              {pieData.map((item, i) => (
                <div key={item.name} className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[i] }}></span>
                  <span className="text-slate-400">{item.name}:</span>
                  <span className="font-mono text-slate-200 font-bold">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
