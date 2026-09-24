'use client';

import React, { useEffect, useState } from 'react';
import Header from '@/components/Header';
import { Share2, AlertTriangle } from 'lucide-react';
import { ReactFlow, Background, Controls, Node, Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const initialNodes: Node[] = [
  { id: 'ACC_2001', position: { x: 250, y: 150 }, data: { label: 'Account: ACC_2001 (Target)' }, style: { background: '#1e1b4b', color: '#818cf8', border: '2px solid #6366f1', borderRadius: '10px', padding: '10px', fontSize: '12px' } },
  { id: 'DEV_RING_999', position: { x: 500, y: 150 }, data: { label: 'Device: DEV_RING_999 (Shared Hub)' }, style: { background: '#881337', color: '#fda4af', border: '2px solid #f43f5e', borderRadius: '10px', padding: '10px', fontSize: '12px', fontWeight: 'bold' } },
  { id: 'ACC_2002', position: { x: 750, y: 80 }, data: { label: 'Account: ACC_2002 (Mule 1)' }, style: { background: '#1e293b', color: '#cbd5e1', border: '1px solid #475569', borderRadius: '10px', padding: '10px', fontSize: '12px' } },
  { id: 'ACC_2003', position: { x: 750, y: 220 }, data: { label: 'Account: ACC_2003 (Mule 2)' }, style: { background: '#1e293b', color: '#cbd5e1', border: '1px solid #475569', borderRadius: '10px', padding: '10px', fontSize: '12px' } },
  { id: 'BEN_RING_777', position: { x: 500, y: 320 }, data: { label: 'Beneficiary: BEN_RING_777' }, style: { background: '#3b0764', color: '#e9d5ff', border: '2px solid #a855f7', borderRadius: '10px', padding: '10px', fontSize: '12px' } },
];

const initialEdges: Edge[] = [
  { id: 'e1', source: 'ACC_2001', target: 'DEV_RING_999', label: 'USES', animated: true, style: { stroke: '#f43f5e', strokeWidth: 2 } },
  { id: 'e2', source: 'ACC_2002', target: 'DEV_RING_999', label: 'USES', animated: true, style: { stroke: '#f43f5e', strokeWidth: 2 } },
  { id: 'e3', source: 'ACC_2003', target: 'DEV_RING_999', label: 'USES', animated: true, style: { stroke: '#f43f5e', strokeWidth: 2 } },
  { id: 'e4', source: 'ACC_2001', target: 'BEN_RING_777', label: 'SENDS_TO', style: { stroke: '#a855f7', strokeWidth: 1.5 } },
];

export default function FraudNetworksPage() {
  const [nodes, setNodes] = useState<Node[]>(initialNodes);
  const [edges, setEdges] = useState<Edge[]>(initialEdges);
  const [selectedNode, setSelectedNode] = useState<Node | null>(initialNodes[1]);

  const onNodeClick = (_: any, node: Node) => {
    setSelectedNode(node);
  };

  return (
    <div className="flex-1 pb-12 flex flex-col h-screen">
      <Header title="Interactive Entity Graph & Fraud Ring Visualizer" subtitle="Multi-Hop Graph Topology & Infrastructure Clustering" />

      <main className="flex-1 px-8 py-6 max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-4 gap-6 min-h-0">
        {/* Interactive Graph Canvas (3 cols) */}
        <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden relative flex flex-col h-[650px]">
          <div className="p-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-2 text-xs">
              <Share2 className="w-4 h-4 text-indigo-400" />
              <span className="font-bold text-slate-100">Neo4j Entity Neighborhood Canvas</span>
              <span className="text-slate-500 font-mono">| Node: ACC_2001 (2 Hops)</span>
            </div>
            <div className="flex items-center space-x-2 text-xs font-mono text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded border border-rose-500/20">
              <AlertTriangle className="w-3.5 h-3.5 animate-pulse" />
              <span>Fraud Ring Infrastructure Detected</span>
            </div>
          </div>

          <div className="flex-1 w-full bg-slate-950">
            <ReactFlow nodes={nodes} edges={edges} onNodeClick={onNodeClick} fitView>
              <Background color="#1e293b" gap={20} />
              <Controls />
            </ReactFlow>
          </div>
        </div>

        {/* Node Inspection Panel (1 col) */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between h-[650px]">
          <div className="space-y-4">
            <h2 className="text-sm font-bold text-slate-100 border-b border-slate-800 pb-3">Entity Inspector</h2>

            {selectedNode ? (
              <div className="space-y-4 text-xs">
                <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 space-y-1">
                  <p className="text-[10px] text-slate-500 uppercase font-mono">Selected Node ID</p>
                  <p className="font-mono font-bold text-indigo-400">{selectedNode.id}</p>
                  <p className="text-slate-300 font-medium">{String(selectedNode.data.label)}</p>
                </div>

                <div className="space-y-2">
                  <p className="font-semibold text-slate-300">Graph Risk Signals:</p>
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1.5 text-slate-400">
                    <p className="flex justify-between"><span>Degree Centrality:</span> <span className="font-mono text-slate-200">3 Connections</span></p>
                    <p className="flex justify-between"><span>Sharing Accounts:</span> <span className="font-mono text-rose-400 font-bold">ACC_2001, ACC_2002, ACC_2003</span></p>
                    <p className="flex justify-between"><span>Infrastructure Risk:</span> <span className="font-mono text-rose-400 font-bold">CRITICAL (0.95)</span></p>
                  </div>
                </div>

                <div className="space-y-1">
                  <p className="font-semibold text-slate-300">Connected Relationships:</p>
                  <ul className="space-y-1 text-slate-400 font-mono text-[11px]">
                    <li>• ACC_2001 -[USES]-&gt; DEV_RING_999</li>
                    <li>• ACC_2002 -[USES]-&gt; DEV_RING_999</li>
                    <li>• ACC_2003 -[USES]-&gt; DEV_RING_999</li>
                    <li>• ACC_2001 -[SENDS_TO]-&gt; BEN_RING_777</li>
                  </ul>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-500">Click any node on the graph canvas to inspect topological details.</p>
            )}
          </div>

          <div className="border-t border-slate-800 pt-4 text-[11px] text-slate-400 space-y-2">
            <p className="font-semibold text-slate-300">Graph Ring Heuristic:</p>
            <p>Shared infrastructure nodes with degree &gt;= 3 are classified as high-risk syndicate hubs.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
