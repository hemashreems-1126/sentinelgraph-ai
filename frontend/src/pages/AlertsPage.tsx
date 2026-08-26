import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BellRing,
  Filter,
  Play,
  ArrowUpDown,
  Search,
  Sparkles,
  Bot,
  CheckCircle2,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { apiClient } from '../api/client';
import { Alert, AlertSeverity } from '../types';
import { RiskBadge } from '../components/RiskBadge';

export const AlertsPage: React.FC = () => {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [prioritizing, setPrioritizing] = useState(false);
  const [investigatingId, setInvestigatingId] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [splitFilter, setSplitFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Selected Planner Mode
  const [selectedPlannerMode, setSelectedPlannerMode] = useState<'static' | 'adaptive'>('static');

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getAlerts({
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
        alert_type: typeFilter || undefined,
        split_type: splitFilter || undefined,
        limit: 100
      });
      setAlerts(data);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [statusFilter, severityFilter, typeFilter, splitFilter]);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await apiClient.generateSyntheticAlerts(200, 1500, 42);
      await fetchAlerts();
    } catch (err) {
      console.error('Failed to generate:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handlePrioritize = async () => {
    setPrioritizing(true);
    try {
      await apiClient.prioritizeAlerts(100);
      await fetchAlerts();
    } catch (err) {
      console.error('Failed to prioritize:', err);
    } finally {
      setPrioritizing(false);
    }
  };

  const handleStartInvestigation = async (alertId: string) => {
    setInvestigatingId(alertId);
    try {
      const res = await apiClient.startInvestigation(alertId, selectedPlannerMode);
      navigate(`/investigations/${res.case_id}`);
    } catch (err) {
      console.error('Failed to start investigation:', err);
      setInvestigatingId(null);
    }
  };

  const filteredAlerts = alerts.filter(
    (a) =>
      a.alert_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.entity_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.trigger_reason.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header & Primary Actions */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Alert Triage & Prioritization Queue</h1>
          <p className="text-sm text-slate-400 mt-1">
            Phase 1 Alert Triage: Deduplicate, categorize, rank by risk urgency, and trigger multi-agent investigation.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Planner Mode Selector */}
          <div className="flex items-center bg-surface border border-slate-800 rounded-xl p-1 text-xs">
            <button
              onClick={() => setSelectedPlannerMode('static')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                selectedPlannerMode === 'static'
                  ? 'bg-indigo-600 text-white font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Static Plan (Default)
            </button>
            <button
              onClick={() => setSelectedPlannerMode('adaptive')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                selectedPlannerMode === 'adaptive'
                  ? 'bg-indigo-600 text-white font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Adaptive Planner (LLM)
            </button>
          </div>

          <button
            onClick={handlePrioritize}
            disabled={prioritizing}
            className="px-3.5 py-2 rounded-xl bg-surface border border-slate-700 hover:border-slate-600 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <ArrowUpDown className={`h-3.5 w-3.5 ${prioritizing ? 'animate-spin' : ''}`} />
            {prioritizing ? 'Triage Ranking...' : 'Prioritize Queue'}
          </button>

          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all"
          >
            <Sparkles className="h-3.5 w-3.5" />
            {generating ? 'Generating...' : 'Seed New Batch'}
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-2xl bg-surface border border-slate-800 flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[220px] relative">
          <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by Alert ID, Account ID, or reason..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-background border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>

        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="px-3 py-1.5 bg-background border border-slate-800 rounded-xl text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
        >
          <option value="">All Severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>

        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-1.5 bg-background border border-slate-800 rounded-xl text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
        >
          <option value="">All Typologies</option>
          <option value="STRUCTURING">Structuring</option>
          <option value="LAYERING">Layering</option>
          <option value="MULE_ACCOUNT">Mule Account</option>
          <option value="VELOCITY_ABUSE">Velocity Abuse</option>
          <option value="ISOLATION_FOREST">Isolation Forest ML</option>
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-1.5 bg-background border border-slate-800 rounded-xl text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
        >
          <option value="">All Statuses</option>
          <option value="PENDING">Pending</option>
          <option value="TRIAGED">Triaged</option>
          <option value="INVESTIGATING">Investigating</option>
          <option value="CLOSED">Closed</option>
          <option value="ESCALATED">Escalated</option>
        </select>

        <select
          value={splitFilter}
          onChange={(e) => setSplitFilter(e.target.value)}
          className="px-3 py-1.5 bg-background border border-slate-800 rounded-xl text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
        >
          <option value="">All Splits</option>
          <option value="TRAIN">Train Split</option>
          <option value="TEST">Held-Out Test Split</option>
        </select>

        <button
          onClick={fetchAlerts}
          className="p-2 rounded-xl bg-background border border-slate-800 text-slate-400 hover:text-slate-200"
          title="Refresh table"
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Alerts Table */}
      <div className="bg-surface border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading alerts queue...</div>
        ) : filteredAlerts.length === 0 ? (
          <div className="p-12 text-center text-slate-500 space-y-3">
            <AlertCircle className="h-8 w-8 mx-auto text-slate-600" />
            <p className="text-sm">No alerts match your filter criteria.</p>
            <button
              onClick={handleGenerate}
              className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold"
            >
              Seed Synthetic Transactions
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px] bg-surface-light/30">
                  <th className="py-3.5 px-4">Rank</th>
                  <th className="py-3.5 px-4">Alert ID</th>
                  <th className="py-3.5 px-4">Entity Ref</th>
                  <th className="py-3.5 px-4">Typology</th>
                  <th className="py-3.5 px-4">Severity / Score</th>
                  <th className="py-3.5 px-4">Trigger Narrative</th>
                  <th className="py-3.5 px-4">Split</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredAlerts.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-slate-400">#{a.priority_rank}</td>
                    <td className="py-3 px-4 font-mono font-medium text-indigo-400">{a.alert_id}</td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      <span className="text-[10px] text-slate-500 block">{a.entity_type}</span>
                      {a.entity_id}
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-mono px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 text-[11px]">
                        {a.alert_type}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <RiskBadge band={a.severity} score={a.raw_score} size="sm" />
                    </td>
                    <td className="py-3 px-4 max-w-xs truncate text-slate-300" title={a.trigger_reason}>
                      {a.trigger_reason}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded ${a.split_type === 'TEST' ? 'bg-indigo-950 text-indigo-400 border border-indigo-500/30' : 'bg-slate-800 text-slate-400'}`}>
                        {a.split_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-300">{a.status}</td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleStartInvestigation(a.alert_id)}
                        disabled={investigatingId === a.alert_id}
                        className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold flex items-center gap-1.5 ml-auto transition-colors shadow-sm"
                      >
                        <Bot className="h-3.5 w-3.5" />
                        {investigatingId === a.alert_id ? 'Investigating...' : 'Investigate'}
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
