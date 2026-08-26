import React, { useEffect, useState } from 'react';
import { ShieldCheck, Search, Filter, RefreshCw, KeyRound, CheckCircle2 } from 'lucide-react';
import { apiClient } from '../api/client';
import { AuditLogRow } from '../types';

export const AuditLogPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [actorFilter, setActorFilter] = useState('');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getAuditLogs({
        actor: actorFilter || undefined,
        limit: 200,
      });
      setLogs(data);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [actorFilter]);

  const filteredLogs = logs.filter(
    (l) =>
      (l.case_id && l.case_id.toLowerCase().includes(searchQuery.toLowerCase())) ||
      l.actor.toLowerCase().includes(searchQuery.toLowerCase()) ||
      l.action_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      l.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      l.verification_hash.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Immutable Compliance Audit Log</h1>
          <p className="text-sm text-slate-400 mt-1">
            Deterministic, tamper-evident record of all multi-agent actions, tool executions, risk scores, and human overrides.
          </p>
        </div>

        <button
          onClick={fetchLogs}
          disabled={loading}
          className="px-3.5 py-2 rounded-xl bg-surface border border-slate-800 hover:border-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-2 transition-colors self-start md:self-auto"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Audit Records</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-2xl bg-surface border border-slate-800 flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[240px] relative">
          <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by Case ID, Agent Actor, Action, or SHA-256 hash..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-background border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>

        <select
          value={actorFilter}
          onChange={(e) => setActorFilter(e.target.value)}
          className="px-3 py-1.5 bg-background border border-slate-800 rounded-xl text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
        >
          <option value="">All Actors</option>
          <option value="SupervisorAgent">Supervisor Agent</option>
          <option value="InvestigationPlanner">Investigation Planner</option>
          <option value="HypothesisGenerationAgent">Hypothesis Agent</option>
          <option value="EvidenceRetrievalAgent">Evidence Agent</option>
          <option value="GraphRelationshipAgent">Graph Agent</option>
          <option value="BehaviorAnalysisAgent">Behavior Agent</option>
          <option value="DocumentAnalysisAgent">Document Agent</option>
          <option value="ExternalIntelligenceAgent">Intelligence Agent</option>
          <option value="CaseAssemblyAgent">Assembly Agent</option>
          <option value="RiskAssignmentAgent">Risk Assignment Agent</option>
          <option value="AuditingAgent">Auditing Agent</option>
          <option value="ReportSARDraftingAgent">SAR Drafting Agent</option>
          <option value="ComplianceOfficer">Compliance Officer (Human)</option>
        </select>
      </div>

      {/* Logs Table */}
      <div className="bg-surface border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading audit records...</div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            No audit logs found. Run an investigation to generate cryptographic audit entries.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px] bg-surface-light/30">
                  <th className="py-3.5 px-4">Case Ref</th>
                  <th className="py-3.5 px-4">Actor</th>
                  <th className="py-3.5 px-4">Action Type</th>
                  <th className="py-3.5 px-4">Description / Output Summary</th>
                  <th className="py-3.5 px-4">Execution (ms)</th>
                  <th className="py-3.5 px-4">SHA-256 Verification Hash</th>
                  <th className="py-3.5 px-4 text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {filteredLogs.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-semibold text-indigo-400">{l.case_id || 'N/A'}</td>
                    <td className="py-3 px-4 text-slate-200 font-medium">{l.actor}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 text-[10px]">
                        {l.action_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-300 max-w-sm truncate font-sans text-xs" title={l.description}>
                      {l.description}
                    </td>
                    <td className="py-3 px-4 text-slate-400">{l.execution_time_ms.toFixed(1)}ms</td>
                    <td className="py-3 px-4 text-slate-500 max-w-[150px] truncate" title={l.verification_hash}>
                      <span className="text-emerald-400 text-[10px] mr-1">●</span>
                      {l.verification_hash}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-500 text-[11px]">
                      {new Date(l.timestamp).toLocaleString()}
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
