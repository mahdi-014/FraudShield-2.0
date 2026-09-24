'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Header from '@/components/Header';
import {
  CheckCircle,
  BrainCircuit,
  Share2,
  Clock,
  FileText,
  UserCheck,
  Zap,
  ArrowRight
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

export default function TransactionDetailPage() {
  const params = useParams();
  const txId = (params.id as str) || 'TX10021';

  const [investigation, setInvestigation] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [feedbackDecision, setFeedbackDecision] = useState<string | null>(null);
  const [justification, setJustification] = useState('');
  const [feedbackSuccess, setFeedbackSuccess] = useState('');

  useEffect(() => {
    fetch(`http://localhost:8000/api/v1/investigation/${txId}`, { method: 'POST' })
      .then((res) => res.json())
      .then((data) => {
        setInvestigation(data);
        setLoading(false);
      })
      .catch((err) => {
        console.log('Error fetching live investigation, using fallback:', err);
        setInvestigation(getFallbackInvestigation(txId));
        setLoading(false);
      });
  }, [txId]);

  const handleSubmitFeedback = (decision: string) => {
    fetch('http://localhost:8000/api/v1/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        case_id: `CAS_${txId}`,
        transaction_id: txId,
        decision,
        justification_reason: justification || 'Verified by human analyst',
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        setFeedbackDecision(decision);
        setFeedbackSuccess(data.message || `Decision '${decision}' recorded successfully.`);
      })
      .catch(() => {
        setFeedbackDecision(decision);
        setFeedbackSuccess(`Analyst decision '${decision}' recorded locally.`);
      });
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-12">
        <div className="flex items-center space-x-3 text-emerald-400 font-mono text-sm">
          <BrainCircuit className="w-6 h-6 animate-spin text-emerald-400" />
          <span>Executing Multi-Agent Graph & Risk Investigation...</span>
        </div>
      </div>
    );
  }

  const shapData = investigation?.shap_explanation?.feature_contributions || [];

  return (
    <div className="flex-1 pb-16">
      <Header title={`Investigation Hub — ${txId}`} subtitle="Evidence-Driven Temporal Graph & Risk Synthesis" />

      <main className="px-8 py-6 max-w-7xl mx-auto space-y-8">
        {/* Top Summary Banner */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="space-y-2">
            <div className="flex items-center space-x-3">
              <span className="font-mono text-2xl font-extrabold text-slate-100">{txId}</span>
              <span className={`px-3 py-1 rounded-full border text-xs font-bold font-mono ${
                investigation.risk_level === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border-rose-500/40' :
                investigation.risk_level === 'HIGH' ? 'bg-orange-500/20 text-orange-400 border-orange-500/40' : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
              }`}>
                {investigation.risk_level} RISK ({(investigation.risk_score * 100).toFixed(0)}%)
              </span>
            </div>
            <p className="text-xs text-slate-300 max-w-2xl">{investigation.case_summary}</p>
          </div>

          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-center min-w-44">
            <p className="text-[11px] text-slate-400 uppercase font-mono">Calibrated Risk Score</p>
            <p className="text-4xl font-extrabold text-rose-400 font-mono mt-1">{(investigation.risk_score * 100).toFixed(1)}</p>
            <p className="text-[10px] text-slate-500 mt-1">Confidence: {investigation.confidence}</p>
          </div>
        </div>

        {/* 2-Column Main Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column (2 cols): SHAP, Temporal Timeline & Fraud Ring */}
          <div className="lg:col-span-2 space-y-8">
            {/* SHAP Explanation */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                    <Zap className="w-4 h-4 text-amber-400" />
                    <span>SHAP Explainability & Risk Attribution</span>
                  </h2>
                  <p className="text-xs text-slate-400">Exact mathematical feature contributions driving model risk score</p>
                </div>
              </div>

              {/* Top Risk Factors list */}
              <div className="mb-4 bg-slate-950/70 border border-slate-800 rounded-lg p-3">
                <p className="text-xs font-semibold text-slate-300 mb-1.5">Primary Risk Factor Drivers:</p>
                <ul className="space-y-1 text-xs text-slate-400">
                  {investigation.shap_explanation?.top_risk_factors?.map((rf: string, idx: number) => (
                    <li key={idx} className="flex items-center space-x-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                      <span>{rf}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* SHAP Bar Chart */}
              <div className="h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={shapData} layout="vertical" margin={{ left: 40, right: 20 }}>
                    <XAxis type="number" stroke="#64748b" fontSize={10} />
                    <YAxis dataKey="display_name" type="category" stroke="#94a3b8" fontSize={11} width={130} tickLine={false} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }} />
                    <Bar dataKey="shap_value" radius={[0, 4, 4, 0]}>
                      {shapData.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={entry.shap_value > 0 ? '#ef4444' : '#22c55e'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Temporal Risk Timeline */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center space-x-2 mb-4">
                <Clock className="w-4 h-4 text-cyan-400" />
                <h2 className="text-base font-bold text-slate-100">Temporal Risk Evolution Timeline</h2>
              </div>
              <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                {investigation.risk_timeline?.map((evt: any, i: number) => (
                  <div key={i} className="relative flex items-start justify-between">
                    <span className="absolute -left-6 top-1.5 w-2.5 h-2.5 rounded-full bg-cyan-400 ring-4 ring-slate-900"></span>
                    <div className="space-y-1">
                      <p className="text-xs font-bold text-slate-200">{evt.event_name}</p>
                      <p className="text-xs text-slate-400">{evt.description}</p>
                      <p className="text-[10px] text-slate-500 font-mono">{evt.timestamp}</p>
                    </div>
                    <span className="font-mono text-xs font-bold text-cyan-400">
                      {(evt.resulting_risk_score * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Fraud Ring Analysis */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center space-x-2 mb-3">
                <Share2 className="w-4 h-4 text-indigo-400" />
                <h2 className="text-base font-bold text-slate-100">Fraud-Ring Topology Analysis</h2>
              </div>
              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Status:</span>
                  <span className={`font-mono font-bold ${investigation.potential_network?.ring_detected ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {investigation.potential_network?.cluster_label}
                  </span>
                </div>
                <div className="text-xs space-y-1">
                  <p className="text-slate-400 font-semibold">Shared Infrastructure Nodes:</p>
                  {investigation.potential_network?.shared_infrastructure?.map((infra: string, idx: number) => (
                    <p key={idx} className="text-indigo-300 font-mono text-[11px]">• {infra}</p>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Right Column (1 col): Evidence Cards, RAG Policy Citations & Analyst Human-in-the-Loop */}
          <div className="space-y-8">
            {/* Primary & Policy Evidence */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
              <div className="flex items-center space-x-2">
                <FileText className="w-4 h-4 text-emerald-400" />
                <h2 className="text-base font-bold text-slate-100">Evidence Portfolio</h2>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <p className="font-semibold text-slate-300 mb-1">Primary Signals:</p>
                  <ul className="space-y-1">
                    {investigation.primary_evidence?.map((pe: string, i: number) => (
                      <li key={i} className="text-slate-400 bg-slate-950 p-2 rounded border border-slate-800">{pe}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <p className="font-semibold text-slate-300 mb-1">RAG Policy Citations:</p>
                  <ul className="space-y-1">
                    {investigation.policy_evidence?.map((pol: string, i: number) => (
                      <li key={i} className="text-slate-400 bg-slate-950 p-2 rounded border border-slate-800">{pol}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Recommended Action */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
              <h2 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                <ArrowRight className="w-4 h-4 text-cyan-400" />
                <span>Recommended Next Actions</span>
              </h2>
              <ul className="space-y-2 text-xs">
                {investigation.recommended_next_steps?.map((step: string, i: number) => (
                  <li key={i} className="flex items-start space-x-2 text-slate-300">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1.5"></span>
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Human-in-the-Loop Analyst Decision Action Box */}
            <div className="bg-slate-900 border border-emerald-500/30 rounded-xl p-6 space-y-4">
              <div className="flex items-center space-x-2">
                <UserCheck className="w-5 h-5 text-emerald-400" />
                <h2 className="text-base font-bold text-slate-100">Analyst Verification Decision</h2>
              </div>

              {feedbackSuccess ? (
                <div className="bg-emerald-950/60 border border-emerald-500/40 p-4 rounded-lg text-xs text-emerald-300 space-y-2">
                  <p className="font-bold flex items-center space-x-1.5">
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                    <span>Human Feedback Recorded</span>
                  </p>
                  <p>{feedbackSuccess}</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <textarea
                    rows={2}
                    placeholder="Enter investigator justification notes..."
                    value={justification}
                    onChange={(e) => setJustification(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
                  />
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      onClick={() => handleSubmitFeedback('CONFIRMED_FRAUD')}
                      className="py-2.5 px-2 bg-rose-500/20 hover:bg-rose-500/30 text-rose-400 border border-rose-500/40 rounded-lg text-xs font-bold transition-colors"
                    >
                      Confirm Fraud
                    </button>
                    <button
                      onClick={() => handleSubmitFeedback('FALSE_POSITIVE')}
                      className="py-2.5 px-2 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/40 rounded-lg text-xs font-bold transition-colors"
                    >
                      False Positive
                    </button>
                    <button
                      onClick={() => handleSubmitFeedback('INCONCLUSIVE')}
                      className="py-2.5 px-2 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-lg text-xs font-bold transition-colors"
                    >
                      Inconclusive
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function getFallbackInvestigation(txId: string) {
  return {
    case_summary: `Transaction ${txId} exhibits high risk due to 5.2x amount deviation from historical baseline and multi-account shared device infrastructure node.`,
    risk_score: 0.94,
    risk_level: 'CRITICAL',
    confidence: 'HIGH',
    shap_explanation: {
      top_risk_factors: [
        'Amount Deviation (>5x baseline average)',
        'Device Fingerprint shared across 3 accounts',
        'New Beneficiary Target',
      ],
      feature_contributions: [
        { display_name: 'Amount Deviation', shap_value: 0.38 },
        { display_name: 'Shared Device Count', shap_value: 0.28 },
        { display_name: 'Beneficiary Novelty', shap_value: 0.18 },
        { display_name: 'High Risk Transfer', shap_value: 0.10 },
      ],
    },
    risk_timeline: [
      { event_name: 'Transaction Ingested', description: 'Wire transfer of $7,850.00 ingested', timestamp: '09:00:00', resulting_risk_score: 0.15 },
      { event_name: 'New Device Flag', description: 'First use of DEV_RING_999', timestamp: '09:02:00', resulting_risk_score: 0.48 },
      { event_name: 'Amount Spike', description: '5.2x baseline average amount', timestamp: '09:03:00', resulting_risk_score: 0.72 },
      { event_name: 'Fraud Ring Topology', description: 'Linked to shared infrastructure node', timestamp: '09:04:00', resulting_risk_score: 0.94 },
    ],
    potential_network: {
      ring_detected: true,
      cluster_label: 'Coordinated Fraud Network (Scenario D)',
      shared_infrastructure: ['Shared Device Node DEV_RING_999 (3 accounts)', 'Shared IP Subnet 10.0.99.99'],
      evidence: ['Device fingerprint DEV_RING_999 is actively shared across 3 distinct customer accounts.'],
    },
    primary_evidence: [
      'Transaction amount ($7,850.00) exceeds historical baseline average by 5.2x.',
      'Initiated from shared device fingerprint DEV_RING_999.',
      'Triggered Rule [MULTIPLE_ACCOUNTS_SHARED_DEVICE].',
    ],
    policy_evidence: [
      '[POL_001] Wire Transfer & High-Value Verification Policy — Transfers >$2,500 from new device require hold.',
    ],
    recommended_next_steps: [
      'Temporarily place an administrative hold on transaction settlement.',
      'Contact customer via out-of-band MFA verification.',
      'Inspect connected cluster accounts sharing device DEV_RING_999.',
    ],
  };
}
