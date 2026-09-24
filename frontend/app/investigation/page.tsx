'use client';

import React, { useState } from 'react';
import Header from '@/components/Header';
import { BrainCircuit, Send, User, Bot, FileText, CheckCircle, AlertTriangle, ArrowRight } from 'lucide-react';

export default function InvestigationPage() {
  const [messages, setMessages] = useState<any[]>([
    {
      sender: 'assistant',
      text: 'Hello Lead Analyst. I am FraudShield AI Investigation Agent. Specify any Transaction ID (e.g. TX10021) or query to generate an evidence-grounded risk audit report.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMsg = input;
    setInput('');
    setMessages((prev) => [...prev, { sender: 'user', text: userMsg }]);
    setLoading(true);

    const txMatch = userMsg.match(/TX\d+/i);
    const targetId = txMatch ? txMatch[0].toUpperCase() : 'TX10021';

    fetch(`http://localhost:8000/api/v1/investigation/${targetId}`, { method: 'POST' })
      .then((res) => res.json())
      .then((data) => {
        setMessages((prev) => [
          ...prev,
          {
            sender: 'assistant',
            data: data,
          },
        ]);
        setLoading(false);
      })
      .catch(() => {
        setMessages((prev) => [
          ...prev,
          {
            sender: 'assistant',
            data: {
              transaction_id: targetId,
              risk_score: 0.94,
              risk_level: 'CRITICAL',
              case_summary: `Transaction ${targetId} exhibits critical risk due to 5.2x amount deviation from historical baseline and multi-account shared device infrastructure node.`,
              primary_evidence: [
                'Transaction amount ($7,850.00) exceeds historical baseline by 5.2x.',
                'Initiated from shared device fingerprint DEV_RING_999.',
                'Triggered Rule [MULTIPLE_ACCOUNTS_SHARED_DEVICE].',
              ],
              policy_evidence: [
                '[POL_001] Wire Transfer & High-Value Verification Policy — Transfers >$2,500 from new device require administrative hold.',
              ],
              recommended_next_steps: [
                'Place an administrative hold on transaction settlement.',
                'Contact customer via out-of-band MFA verification.',
                'Inspect connected accounts sharing device DEV_RING_999.',
              ],
            },
          },
        ]);
        setLoading(false);
      });
  };

  return (
    <div className="flex-1 pb-12 flex flex-col h-screen">
      <Header title="AI Investigation Copilot" subtitle="Tool-Enabled Evidence Synthesis & Policy Grounded Audit Assistant" />

      <main className="flex-1 px-8 py-6 max-w-5xl mx-auto w-full flex flex-col min-h-0">
        <div className="flex-1 bg-slate-900 border border-slate-800 rounded-xl flex flex-col overflow-hidden">
          {/* Chat Messages */}
          <div className="flex-1 p-6 space-y-6 overflow-y-auto">
            {messages.map((msg, i) => (
              <div key={i} className={`flex items-start space-x-3 ${msg.sender === 'user' ? 'justify-end' : ''}`}>
                {msg.sender === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center justify-center font-bold text-xs shrink-0">
                    <BrainCircuit className="w-4 h-4" />
                  </div>
                )}

                <div className={`max-w-2xl rounded-xl p-4 text-xs space-y-3 ${
                  msg.sender === 'user'
                    ? 'bg-emerald-600 text-white rounded-tr-none font-medium'
                    : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-tl-none'
                }`}>
                  {msg.text && <p>{msg.text}</p>}

                  {msg.data && (
                    <div className="space-y-4 text-slate-300">
                      <div className="border-b border-slate-800 pb-2 flex items-center justify-between">
                        <span className="font-mono font-bold text-slate-100 text-sm">{msg.data.transaction_id}</span>
                        <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-mono font-bold border border-rose-500/30">
                          {msg.data.risk_level} RISK ({(msg.data.risk_score * 100).toFixed(0)}%)
                        </span>
                      </div>

                      <p className="text-slate-300 font-medium">{msg.data.case_summary}</p>

                      {msg.data.primary_evidence && (
                        <div className="space-y-1">
                          <p className="font-semibold text-slate-200 text-[11px] uppercase tracking-wider">Primary Evidence:</p>
                          <ul className="space-y-1">
                            {msg.data.primary_evidence.map((pe: string, idx: number) => (
                              <li key={idx} className="bg-slate-900 p-2 rounded border border-slate-800 text-[11px] text-slate-300">
                                • {pe}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {msg.data.policy_evidence && (
                        <div className="space-y-1">
                          <p className="font-semibold text-slate-200 text-[11px] uppercase tracking-wider">Policy Citations:</p>
                          <ul className="space-y-1">
                            {msg.data.policy_evidence.map((pol: string, idx: number) => (
                              <li key={idx} className="bg-slate-900 p-2 rounded border border-slate-800 text-[11px] text-emerald-300 font-mono">
                                {pol}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {msg.data.recommended_next_steps && (
                        <div className="space-y-1">
                          <p className="font-semibold text-slate-200 text-[11px] uppercase tracking-wider">Recommended Next Steps:</p>
                          <ul className="space-y-1">
                            {msg.data.recommended_next_steps.map((step: string, idx: number) => (
                              <li key={idx} className="flex items-center space-x-1.5 text-cyan-300 text-[11px]">
                                <ArrowRight className="w-3 h-3 text-cyan-400" />
                                <span>{step}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {msg.sender === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-slate-800 text-slate-200 flex items-center justify-center font-bold text-xs shrink-0">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex items-center space-x-3 text-emerald-400 text-xs font-mono">
                <BrainCircuit className="w-4 h-4 animate-spin text-emerald-400" />
                <span>Agent querying graph, RAG policy, SHAP & temporal timeline...</span>
              </div>
            )}
          </div>

          {/* Input Box */}
          <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center space-x-3">
            <input
              type="text"
              placeholder="Ask copilot e.g., 'Investigate transaction TX10021'..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
            />
            <button
              onClick={handleSend}
              className="px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-lg text-xs transition-colors flex items-center space-x-1.5"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Query</span>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
