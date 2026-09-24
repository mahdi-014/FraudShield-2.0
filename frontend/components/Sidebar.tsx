'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  ShieldAlert,
  LayoutDashboard,
  CreditCard,
  Bell,
  Briefcase,
  Share2,
  BrainCircuit,
  Cpu,
  Sliders,
  LogOut
} from 'lucide-react';

const navigation = [
  { name: 'Executive Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Live Transactions', href: '/transactions', icon: CreditCard },
  { name: 'Fraud Alerts', href: '/alerts', icon: Bell },
  { name: 'Case Triage', href: '/cases', icon: Briefcase },
  { name: 'Fraud Networks', href: '/fraud-networks', icon: Share2 },
  { name: 'AI Investigator', href: '/investigation', icon: BrainCircuit },
  { name: 'Model Registry', href: '/models', icon: Cpu },
  { name: 'Governance & Metrics', href: '/governance', icon: Sliders },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen sticky top-0 z-30">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800 flex items-center space-x-3">
        <div className="p-2 bg-emerald-500/10 rounded-lg border border-emerald-500/30">
          <ShieldAlert className="w-6 h-6 text-emerald-400" />
        </div>
        <div>
          <h1 className="font-bold text-slate-100 text-lg tracking-tight">FraudShield <span className="text-emerald-400 font-mono text-xs px-1.5 py-0.5 bg-emerald-950 border border-emerald-500/30 rounded">2.0</span></h1>
          <p className="text-xs text-slate-400">Temporal Graph Intelligence</p>
        </div>
      </div>

      {/* Live System Status Pill */}
      <div className="px-4 py-3 mx-4 my-3 bg-slate-950/70 border border-slate-800 rounded-lg flex items-center justify-between text-xs text-slate-300">
        <div className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Engine Active</span>
        </div>
        <span className="text-slate-500 font-mono">v2.0.0</span>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Analyst Profile & Logout */}
      <div className="p-4 border-t border-slate-800 flex items-center justify-between bg-slate-950/40">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-emerald-600 text-white font-bold flex items-center justify-center text-xs">
            A1
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-200">Lead Analyst</p>
            <p className="text-[10px] text-slate-400">analyst1@fraudshield.ai</p>
          </div>
        </div>
        <Link href="/login" className="text-slate-500 hover:text-rose-400 p-1.5 transition-colors">
          <LogOut className="w-4 h-4" />
        </Link>
      </div>
    </aside>
  );
}
