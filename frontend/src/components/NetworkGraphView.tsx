import React, { useMemo, useState } from 'react';

interface GraphNode {
  id: string;
  label: string;
  customer_id: string;
  risk_tier: string;
  is_pep: boolean;
  is_sanctioned: boolean;
  is_target: boolean;
}
interface GraphEdge { source: string; target: string; amount: number; count: number; txn_type: string }

interface NetworkGraphViewProps {
  graphData: {
    nodes?: GraphNode[];
    edges?: GraphEdge[];
    total_counterparties?: number;
    high_risk_connections_count?: number;
    shortest_path_to_watchlist?: string;
    has_cycles?: boolean;
    display_note?: string;
  };
}

const W = 900;
const H = 560;
const CX = W / 2;
const CY = H / 2;
const inr = (x: number) => `₹${Math.round(x).toLocaleString('en-IN')}`;

/**
 * Radial money-flow diagram: the investigated account in the centre, direct counterparties on the
 * inner ring, second-hop accounts on the outer ring next to the account they connect through.
 * Arrow thickness grows with the amount moved.
 */
export const NetworkGraphView: React.FC<NetworkGraphViewProps> = ({ graphData }) => {
  const nodes = graphData.nodes || [];
  const edges = graphData.edges || [];
  const [hover, setHover] = useState<string | null>(null);

  const layout = useMemo(() => {
    const target = nodes.find((n) => n.is_target) ?? nodes[0];
    if (!target) return null;
    const touches = (e: GraphEdge, id: string) => e.source === id || e.target === id;
    const directIds = new Set(
      edges.filter((e) => touches(e, target.id)).map((e) => (e.source === target.id ? e.target : e.source)),
    );
    const direct = nodes.filter((n) => directIds.has(n.id));
    const outer = nodes.filter((n) => n.id !== target.id && !directIds.has(n.id));

    const pos: Record<string, { x: number; y: number; angle: number }> = { [target.id]: { x: CX, y: CY, angle: 0 } };
    const r1 = Math.min(W, H) * 0.27;
    const r2 = Math.min(W, H) * 0.46;
    direct.forEach((n, i) => {
      const a = (2 * Math.PI * i) / Math.max(1, direct.length) - Math.PI / 2;
      pos[n.id] = { x: CX + r1 * Math.cos(a) * 1.35, y: CY + r1 * Math.sin(a), angle: a };
    });
    // place each outer node near the direct node it is linked to
    const byParent: Record<string, GraphNode[]> = {};
    outer.forEach((n) => {
      const parent = edges.find((e) => touches(e, n.id) && (directIds.has(e.source) || directIds.has(e.target)));
      const pid = parent ? (directIds.has(parent.source) ? parent.source : parent.target) : '__none__';
      (byParent[pid] ??= []).push(n);
    });
    Object.entries(byParent).forEach(([pid, kids]) => {
      const base = pos[pid]?.angle ?? 0;
      kids.forEach((n, k) => {
        const a = base + (k - (kids.length - 1) / 2) * 0.16;
        pos[n.id] = { x: CX + r2 * Math.cos(a) * 1.35, y: CY + r2 * Math.sin(a), angle: a };
      });
    });
    const maxAmt = Math.max(1, ...edges.map((e) => e.amount));
    return { target, pos, maxAmt, directCount: direct.length };
  }, [nodes, edges]);

  if (!layout) {
    return (
      <div className="p-8 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
        No network graph data available for this entity.
      </div>
    );
  }

  const { target, pos, maxAmt } = layout;
  const nodeColor = (n: GraphNode) =>
    n.is_target ? '#818cf8' : n.is_sanctioned ? '#f43f5e' : n.is_pep ? '#f59e0b' : n.risk_tier === 'HIGH' ? '#fb7185' : '#64748b';
  const active = (e: GraphEdge) => !hover || e.source === hover || e.target === hover;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-[11px] font-mono uppercase text-slate-400">Accounts within 2 hops</div>
          <div className="text-2xl font-bold text-slate-100">{graphData.total_counterparties ?? nodes.length - 1}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-[11px] font-mono uppercase text-slate-400">High-risk accounts nearby</div>
          <div className="text-2xl font-bold text-rose-400">{graphData.high_risk_connections_count ?? 0}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-[11px] font-mono uppercase text-slate-400">Time-ordered round trip</div>
          <div className={`text-2xl font-bold ${graphData.has_cycles ? 'text-amber-300' : 'text-slate-300'}`}>{graphData.has_cycles ? 'Found' : 'None'}</div>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 min-w-0">
          <div className="text-[11px] font-mono uppercase text-slate-400">Path to watchlist</div>
          <div className="text-xs font-mono text-amber-300 truncate mt-1" title={graphData.shortest_path_to_watchlist}>{graphData.shortest_path_to_watchlist ?? '—'}</div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-950/60 overflow-hidden">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto" role="img" aria-label="Money-flow network around the investigated account">
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="9" markerHeight="9" markerUnits="userSpaceOnUse" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" />
            </marker>
          </defs>
          {edges.map((e, i) => {
            const a = pos[e.source];
            const b = pos[e.target];
            if (!a || !b) return null;
            const width = 0.6 + 4 * Math.sqrt(e.amount / maxAmt);
            const isTargetEdge = e.source === target.id || e.target === target.id;
            return (
              <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
                stroke={isTargetEdge ? '#818cf8' : '#475569'} strokeWidth={width}
                strokeOpacity={active(e) ? (isTargetEdge ? 0.85 : 0.45) : 0.06} markerEnd="url(#arrow)">
                <title>{`${e.source} → ${e.target}: ${inr(e.amount)} in ${e.count} transaction(s)`}</title>
              </line>
            );
          })}
          {nodes.map((n) => {
            const p = pos[n.id];
            if (!p) return null;
            const r = n.is_target ? 16 : 7;
            return (
              <g key={n.id} onMouseEnter={() => setHover(n.id)} onMouseLeave={() => setHover(null)} className="cursor-pointer">
                <circle cx={p.x} cy={p.y} r={r} fill={nodeColor(n)} stroke="#0f172a" strokeWidth={2}
                  opacity={!hover || hover === n.id || edges.some((e) => (e.source === hover && e.target === n.id) || (e.target === hover && e.source === n.id)) ? 1 : 0.25} />
                {(n.is_target || hover === n.id) && (
                  <text x={p.x} y={p.y - r - 6} textAnchor="middle" fontSize={n.is_target ? 13 : 11} fill="#e2e8f0" fontWeight={600}>
                    {n.is_target ? `${n.label} (subject)` : `${n.label} · ${n.id}`}
                  </text>
                )}
                <title>{`${n.label} — ${n.id} · risk ${n.risk_tier}${n.is_pep ? ' · PEP' : ''}${n.is_sanctioned ? ' · SANCTIONED' : ''}`}</title>
              </g>
            );
          })}
        </svg>
        <div className="px-4 py-2 border-t border-slate-800 text-[11px] text-slate-400 flex flex-wrap gap-4">
          <span><span className="inline-block h-2 w-2 rounded-full bg-indigo-400 mr-1" />subject</span>
          <span><span className="inline-block h-2 w-2 rounded-full bg-slate-500 mr-1" />counterparty</span>
          <span><span className="inline-block h-2 w-2 rounded-full bg-rose-400 mr-1" />high risk</span>
          <span><span className="inline-block h-2 w-2 rounded-full bg-amber-500 mr-1" />PEP</span>
          <span>Arrow thickness = money moved · hover a node to focus</span>
          {graphData.display_note && <span className="ml-auto">{graphData.display_note}</span>}
        </div>
      </div>
    </div>
  );
};
