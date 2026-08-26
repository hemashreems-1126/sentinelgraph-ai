import React from 'react';
import { Shield, AlertOctagon, UserCheck, ArrowRight } from 'lucide-react';

interface NetworkGraphViewProps {
  graphData: {
    nodes?: Array<{
      id: string;
      label: string;
      customer_id: string;
      risk_tier: string;
      is_pep: boolean;
      is_sanctioned: boolean;
      is_target: boolean;
    }>;
    edges?: Array<{
      source: string;
      target: string;
      amount: number;
      count: number;
      txn_type: string;
    }>;
    total_counterparties?: number;
    high_risk_connections_count?: number;
    shortest_path_to_watchlist?: string;
  };
}

export const NetworkGraphView: React.FC<NetworkGraphViewProps> = ({ graphData }) => {
  const nodes = graphData.nodes || [];
  const edges = graphData.edges || [];

  if (nodes.length === 0) {
    return (
      <div className="p-8 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
        No network graph data available for this entity.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Network Metrics Bar */}
      <div className="grid grid-cols-3 gap-3">
        <div className="p-3 bg-surface rounded-lg border border-slate-800">
          <span className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Counterparties</span>
          <p className="text-lg font-bold text-slate-100 mt-0.5">{graphData.total_counterparties || nodes.length - 1}</p>
        </div>
        <div className="p-3 bg-surface rounded-lg border border-slate-800">
          <span className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">High-Risk Hops</span>
          <p className={`text-lg font-bold mt-0.5 ${(graphData.high_risk_connections_count || 0) > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
            {graphData.high_risk_connections_count || 0}
          </p>
        </div>
        <div className="p-3 bg-surface rounded-lg border border-slate-800 col-span-1">
          <span className="text-[11px] uppercase tracking-wider text-slate-400 font-mono">Watchlist Proximity</span>
          <p className="text-xs font-mono font-medium text-amber-400 truncate mt-1" title={graphData.shortest_path_to_watchlist}>
            {graphData.shortest_path_to_watchlist || 'Clean'}
          </p>
        </div>
      </div>

      {/* Network Entity Cards Grid */}
      <div className="p-4 bg-background/60 rounded-xl border border-slate-800">
        <h5 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-3">2-Hop Entity Network Nodes</h5>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {nodes.map((node) => {
            const isHigh = node.risk_tier === 'HIGH' || node.is_pep || node.is_sanctioned;
            return (
              <div
                key={node.id}
                className={`p-3 rounded-lg border text-xs transition-all ${
                  node.is_target
                    ? 'bg-indigo-950/40 border-indigo-500 shadow-sm shadow-indigo-500/20'
                    : isHigh
                    ? 'bg-rose-950/20 border-rose-500/40'
                    : 'bg-surface border-slate-800'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-slate-300 font-medium">{node.id}</span>
                  {node.is_target && (
                    <span className="px-1.5 py-0.5 rounded bg-indigo-500 text-[10px] font-bold text-white uppercase">
                      Target Subject
                    </span>
                  )}
                </div>
                <p className="text-slate-100 font-semibold mt-1 truncate">{node.label}</p>
                <div className="flex items-center gap-2 mt-2 font-mono text-[10px]">
                  <span className={`px-1.5 py-0.5 rounded ${isHigh ? 'bg-rose-900/60 text-rose-300' : 'bg-slate-800 text-slate-400'}`}>
                    Tier: {node.risk_tier}
                  </span>
                  {node.is_pep && <span className="px-1.5 py-0.5 rounded bg-amber-900/60 text-amber-300">PEP</span>}
                  {node.is_sanctioned && <span className="px-1.5 py-0.5 rounded bg-rose-600 text-white font-bold">SANCTIONED</span>}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Network Edges / Flow Table */}
      {edges.length > 0 && (
        <div className="p-4 bg-background/60 rounded-xl border border-slate-800">
          <h5 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-3">Observed Inter-Account Fund Flows</h5>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                  <th className="pb-2">Source</th>
                  <th className="pb-2 text-center">Flow</th>
                  <th className="pb-2">Destination</th>
                  <th className="pb-2 text-right">Total Flow Amount</th>
                  <th className="pb-2 text-right">Transactions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {edges.map((edge, i) => (
                  <tr key={i} className="hover:bg-surface/50 font-mono text-slate-300">
                    <td className="py-2 text-indigo-400 font-medium">{edge.source}</td>
                    <td className="py-2 text-center text-slate-500"><ArrowRight className="h-3.5 w-3.5 mx-auto text-slate-400" /></td>
                    <td className="py-2 text-slate-200">{edge.target}</td>
                    <td className="py-2 text-right font-semibold text-emerald-400">${edge.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td className="py-2 text-right text-slate-400">{edge.count}x ({edge.txn_type})</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
