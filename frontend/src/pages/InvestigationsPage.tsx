import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FolderSearch,
  Search,
  Filter,
  ArrowUpRight,
  RefreshCw,
  Cpu,
  RotateCcw
} from 'lucide-react';
import { apiClient } from '../api/client';
import { InvestigationCaseSummary } from '../types';
import { RiskBadge } from '../components/RiskBadge';
import { DecisionBadge } from '../components/DecisionBadge';

export const InvestigationsPage: React.FC = () => {
  const navigate = useNavigate();
  const [cases, setCases] = useState<InvestigationCaseSummary[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [decisionFilter, setDecisionFilter] = useState('');
  const [riskBandFilter, setRiskBandFilter] = useState('');
  const [plannerFilter, setPlannerFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchCases = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getInvestigations({
        decision: decisionFilter || undefined,
        risk_band: riskBandFilter || undefined,
        planner_mode: plannerFilter || undefined,
      });
      setCases(data);
    } catch (err) {
      console.error('Failed to fetch investigations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, [decisionFilter, riskBandFilter, plannerFilter]);

  const filteredCases = cases.filter(
    (c) =>
      c.case_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.alert_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.decision_rationale && c.decision_rationale.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Multi-Agent Forensic Investigations</h1>
          <p className="text-sm text-slate-400 mt-1">
            Complete records of LangGraph multi-agent investigations, loop-back iterations, and deterministic risk assignments.
          </p>
        </div>

        <button
          onClick={fetchCases}
          disabled={loading}
          className="px-3.5 py-2 rounded-xl bg-surface border border-slate-800 hover:border-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-2 transition-colors self-start md:self-auto"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Cases</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-2xl bg-surface border border-slate-800 flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[220px] relative">
          <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by Case ID, Alert ID, or rationale..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-background border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>

        <select
          value={decisionFilter}
          onChange={(e) => setDecisionFilter(e.target.value)}
          className="px-3 py-1.5 bg-background border border-slate-800 rounded-xl text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
        >
          <option value="">All Decisions</option>
          <option value="ALLOW">ALLOW</option>
          <option value="REVIEW">REVIEW</option>
          <option value="BLOCK">BLOCK</option>
        </select>

        <select
          value={riskBandFilter}
          onChange={(e) => setRiskBandFilter(e.target.value)}
          className="px-3 py-1.5 bg-background border border-slate-800 rounded-xl text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
        >
          <option value="">All Risk Bands</option>
          <option value="CRITICAL">Critical (81-100)</option>
          <option value="HIGH">High (61-80)</option>
          <option value="MEDIUM">Medium (31-60)</option>
          <option value="LOW">Low (0-30)</option>
        </select>

        <select
          value={plannerFilter}
          onChange={(e) => setPlannerFilter(e.target.value)}
          className="px-3 py-1.5 bg-background border border-slate-800 rounded-xl text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
        >
          <option value="">All Planners</option>
          <option value="static">Static Checklist</option>
          <option value="adaptive">Adaptive LLM</option>
        </select>
      </div>

      {/* Cases Table */}
      <div className="bg-surface border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading cases dossier...</div>
        ) : filteredCases.length === 0 ? (
          <div className="p-12 text-center text-slate-500 space-y-3">
            <FolderSearch className="h-8 w-8 mx-auto text-slate-600" />
            <p className="text-sm">No investigations found matching your filter criteria.</p>
            <button
              onClick={() => navigate('/alerts')}
              className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold"
            >
              Go to Alerts Queue
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px] bg-surface-light/30">
                  <th className="py-3.5 px-4">Case ID</th>
                  <th className="py-3.5 px-4">Originating Alert</th>
                  <th className="py-3.5 px-4">Planner Mode</th>
                  <th className="py-3.5 px-4">Loop Cycles</th>
                  <th className="py-3.5 px-4">Deterministic Risk Score</th>
                  <th className="py-3.5 px-4">Policy Decision</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredCases.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-semibold text-indigo-400">{c.case_id}</td>
                    <td className="py-3 px-4 font-mono text-slate-300">{c.alert_id}</td>
                    <td className="py-3 px-4">
                      <span className="font-mono px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 text-[11px] uppercase">
                        {c.planner_mode}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded ${c.iterations_count > 1 ? 'bg-amber-950/80 text-amber-400 border border-amber-500/30' : 'text-slate-400'}`}>
                        {c.iterations_count > 1 && <RotateCcw className="h-3 w-3" />}
                        {c.iterations_count} cycle{c.iterations_count > 1 ? 's' : ''}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <RiskBadge band={c.final_risk_band} score={c.final_risk_score} size="sm" />
                    </td>
                    <td className="py-3 px-4">
                      <DecisionBadge decision={c.final_decision} size="sm" />
                    </td>
                    <td className="py-3 px-4 font-mono text-emerald-400 font-semibold">{c.status}</td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => navigate(`/investigations/${c.case_id}`)}
                        className="px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 font-semibold transition-all inline-flex items-center gap-1"
                      >
                        <span>Inspect Trail</span>
                        <ArrowUpRight className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
