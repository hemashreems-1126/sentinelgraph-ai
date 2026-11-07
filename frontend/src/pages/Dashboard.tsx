import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BellRing,
  FolderSearch,
  ShieldAlert,
  Activity,
  Play,
  Filter,
  CheckCircle,
  AlertTriangle,
  ArrowUpRight,
  RefreshCw,
  TrendingUp,
  Cpu
} from 'lucide-react';
import { apiClient } from '../api/client';
import { AlertStatsSummary, InvestigationCaseSummary, EvaluationMetric } from '../types';
import { RiskBadge } from '../components/RiskBadge';
import { FilingBadge } from '../components/FilingBadge';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<AlertStatsSummary | null>(null);
  const [recentCases, setRecentCases] = useState<InvestigationCaseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [evaluation, setEvaluation] = useState<EvaluationMetric | null>(null);

  useEffect(() => {
    apiClient.getLatestEvaluation().then(setEvaluation).catch(() => setEvaluation(null));
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsData, casesData] = await Promise.all([
        apiClient.getAlertStats(),
        apiClient.getInvestigations({ limit: 5 })
      ]);
      setStats(statsData);
      setRecentCases(casesData);
    } catch (err) {
      window.alert(`Could not load dashboard data. ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleGenerateData = async () => {
    if (!window.confirm('Generate a new synthetic ledger? This replaces ALL current alerts, investigations and audit logs.')) return;
    setGenerating(true);
    try {
      await apiClient.generateSyntheticAlerts(200, 1500, 42);
      await apiClient.prioritizeAlerts(50);
      await loadData();
    } catch (err) {
      window.alert(`Could not generate batch. ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setGenerating(false);
    }
  };

  const chartColors = ['#6366F1', '#EC4899', '#F59E0B', '#10B981', '#3B82F6', '#8B5CF6'];

  const typeData = stats
    ? Object.entries(stats.alert_type_breakdown).map(([name, value]) => ({ name, value }))
    : [];

  const severityData = stats
    ? Object.entries(stats.severity_breakdown).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Financial Crime Surveillance Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1">
            Alerts from India-first rules and an Isolation Forest, investigated by agents, decided by evidence, and fact-checked.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            disabled={loading}
            className="p-2.5 rounded-xl bg-surface border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={handleGenerateData}
            disabled={generating}
            className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-bold tracking-wide flex items-center gap-2 shadow-lg shadow-indigo-600/20 transition-all"
          >
            <Play className={`h-3.5 w-3.5 fill-current ${generating ? 'animate-pulse' : ''}`} />
            {generating ? 'Simulating Batch...' : 'Generate Synthetic Batch'}
          </button>
        </div>
      </div>

      {/* What the system actually achieves (latest real evaluation run) */}
      {evaluation?.metrics_json && (
        <button onClick={() => navigate('/evaluation')}
          className="w-full text-left p-4 rounded-2xl border border-indigo-500/30 bg-indigo-950/20 hover:bg-indigo-950/40 transition-colors">
          <div className="text-[11px] uppercase tracking-wide text-indigo-300 mb-2">
            Latest evaluation · {evaluation.metrics_json.filing.cases_investigated} held-out alerts · {evaluation.metrics_json.dataset}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div><div className="text-2xl font-extrabold text-white">{(evaluation.metrics_json.filing.precision * 100).toFixed(0)}% / {(evaluation.metrics_json.filing.recall * 100).toFixed(0)}%</div><div className="text-xs text-slate-400">STR filing precision / recall</div></div>
            <div><div className="text-2xl font-extrabold text-white">{(evaluation.metrics_json.filing.alert_reduction_rate * 100).toFixed(0)}%</div><div className="text-xs text-slate-400">alerts closed with a written reason</div></div>
            <div><div className="text-2xl font-extrabold text-white">{(evaluation.metrics_json.fact_check.genuine_reports_ready * 100).toFixed(0)}%</div><div className="text-xs text-slate-400">reports fully verified against the ledger</div></div>
            <div><div className="text-2xl font-extrabold text-white">{(evaluation.metrics_json.fact_check.corruption_catch_rate * 100).toFixed(0)}%</div><div className="text-xs text-slate-400">corrupted (hallucinated) reports caught</div></div>
          </div>
        </button>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-surface border border-slate-800/80 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono uppercase tracking-wider">Total Alerts</span>
            <div className="p-2 rounded-lg bg-indigo-950/60 border border-indigo-500/30 text-indigo-400">
              <BellRing className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <h3 className="text-3xl font-extrabold text-white font-mono">{stats?.total_alerts || 0}</h3>
            <span className="text-xs text-indigo-400 font-medium">{stats?.pending_alerts || 0} Pending</span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-surface border border-slate-800/80 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono uppercase tracking-wider">Investigated Cases</span>
            <div className="p-2 rounded-lg bg-emerald-950/60 border border-emerald-500/30 text-emerald-400">
              <FolderSearch className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <h3 className="text-3xl font-extrabold text-white font-mono">{stats?.total_cases_investigated || 0}</h3>
            <span className="text-xs text-emerald-400 font-medium">Multi-Agent</span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-surface border border-slate-800/80 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono uppercase tracking-wider">Critical Severity</span>
            <div className="p-2 rounded-lg bg-rose-950/60 border border-rose-500/30 text-rose-400">
              <ShieldAlert className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <h3 className="text-3xl font-extrabold text-white font-mono">
              {stats?.severity_breakdown?.CRITICAL || 0}
            </h3>
            <span className="text-xs text-rose-400 font-medium">High Priority</span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-surface border border-slate-800/80 shadow-sm space-y-3">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono uppercase tracking-wider">Monitored Ledger</span>
            <div className="p-2 rounded-lg bg-amber-950/60 border border-amber-500/30 text-amber-400">
              <Activity className="h-4 w-4" />
            </div>
          </div>
          <div className="flex items-baseline justify-between">
            <h3 className="text-3xl font-extrabold text-white font-mono">{stats?.total_transactions || 0}</h3>
            <span className="text-xs text-amber-400 font-medium">{stats?.total_customers || 0} Entities</span>
          </div>
        </div>
      </div>

      {/* Visual Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Typology Breakdown */}
        <div className="p-6 rounded-2xl bg-surface border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Alert Typology Distribution</h3>
              <p className="text-xs text-slate-400">Rule-based triggers & ML Isolation Forest anomaly counts</p>
            </div>
            <span className="text-xs font-mono text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-500/30">
              Phase 1 Triage
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={typeData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="name" stroke="#64748B" fontSize={10} tickLine={false} interval={0} angle={-15} textAnchor="end" />
                <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', fontSize: '12px' }}
                />
                <Bar dataKey="value" fill="#6366F1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Severity Breakdown */}
        <div className="p-6 rounded-2xl bg-surface border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-white">Severity Classification Funnel</h3>
              <p className="text-xs text-slate-400">Risk classification before multi-agent investigation</p>
            </div>
            <span className="text-xs font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-500/30">
              Triage Ranked
            </span>
          </div>

          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severityData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  innerRadius={45}
                  paddingAngle={5}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {severityData.map((entry, index) => {
                    const color = entry.name === 'CRITICAL' ? '#EF4444' : (entry.name === 'HIGH' ? '#F97316' : (entry.name === 'MEDIUM' ? '#F59E0B' : '#10B981'));
                    return <Cell key={`cell-${index}`} fill={color} />;
                  })}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '8px', fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Investigations Table */}
      <div className="p-6 rounded-2xl bg-surface border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white">Recent Multi-Agent Investigations</h3>
            <p className="text-xs text-slate-400">Completed forensic cases with deterministic risk assignments</p>
          </div>
          <button
            onClick={() => navigate('/investigations')}
            className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
          >
            <span>View All Cases</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </button>
        </div>

        {recentCases.length === 0 ? (
          <div className="p-8 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
            No investigations run yet. Visit the Alerts Queue and click "Investigate" to launch the agentic graph.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                  <th className="pb-3">Case ID</th>
                  <th className="pb-3">Alert Ref</th>
                  <th className="pb-3">Planner</th>
                  <th className="pb-3">Iterations</th>
                  <th className="pb-3">Deterministic Score</th>
                  <th className="pb-3">Filing Decision</th>
                  <th className="pb-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {recentCases.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 font-mono font-medium text-indigo-400">{c.case_id}</td>
                    <td className="py-3 font-mono text-slate-300">{c.alert_id}</td>
                    <td className="py-3 font-mono text-slate-300 uppercase">{c.planner_mode}</td>
                    <td className="py-3 font-mono text-slate-400">{c.iterations_count}x</td>
                    <td className="py-3">
                      <RiskBadge band={c.final_risk_band} score={c.final_risk_score} size="sm" />
                    </td>
                    <td className="py-3">
                      <FilingBadge decision={c.filing_decision} tier={c.filing_tier} />
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => navigate(`/investigations/${c.case_id}`)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-indigo-600 hover:text-white text-slate-300 font-medium transition-colors"
                      >
                        Inspect Dossier
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
