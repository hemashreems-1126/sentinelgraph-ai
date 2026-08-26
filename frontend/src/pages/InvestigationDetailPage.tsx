import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Bot,
  BrainCircuit,
  FileSearch,
  Network,
  Activity,
  FileText,
  Globe2,
  FolderArchive,
  Calculator,
  ShieldCheck,
  FileSpreadsheet,
  RotateCcw,
  UserCheck,
  Clock,
  Layers,
  Sparkles,
  AlertTriangle
} from 'lucide-react';
import { apiClient } from '../api/client';
import { InvestigationCaseDetail } from '../types';
import { RiskBadge } from '../components/RiskBadge';
import { DecisionBadge } from '../components/DecisionBadge';
import { AgentTrailCard } from '../components/AgentTrailCard';
import { NetworkGraphView } from '../components/NetworkGraphView';
import { SarReportViewer } from '../components/SarReportViewer';
import { FeedbackModal } from '../components/FeedbackModal';

export const InvestigationDetailPage: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState<InvestigationCaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'trail' | 'subagents' | 'hypotheses' | 'sar' | 'audit'>('trail');
  const [feedbackOpen, setFeedbackOpen] = useState(false);

  const fetchDetail = async () => {
    if (!caseId) return;
    setLoading(true);
    try {
      const data = await apiClient.getInvestigationDetail(caseId);
      setCaseData(data);
    } catch (err) {
      console.error('Failed to load investigation detail:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [caseId]);

  if (loading) {
    return <div className="p-12 text-center text-slate-400">Loading forensic case dossier...</div>;
  }

  if (!caseData) {
    return (
      <div className="p-12 text-center text-slate-500 space-y-4">
        <p>Case not found.</p>
        <button onClick={() => navigate('/investigations')} className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold">
          Back to Investigations
        </button>
      </div>
    );
  }

  const subagents = caseData.subagent_evidence_json || {};
  const reasoning = caseData.reasoning_json || {};
  const featureBreakdown = caseData.reasoning_json ? caseData.agent_trail_json?.find(s => s.agent_name.includes('RiskAssignment'))?.details?.feature_score_breakdown : null;

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/investigations')}
          className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Investigations</span>
        </button>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setFeedbackOpen(true)}
            className="px-4 py-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-500/30 text-xs font-semibold flex items-center gap-2 transition-all shadow-sm"
          >
            <UserCheck className="h-4 w-4" />
            <span>Investigator Decision / Override</span>
          </button>
        </div>
      </div>

      {/* Case Header Hero Box */}
      <div className="p-6 rounded-2xl bg-surface border border-slate-800 shadow-md space-y-5">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h2 className="text-xl font-extrabold text-white font-mono">{caseData.case_id}</h2>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
                Alert: {caseData.alert_id}
              </span>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-indigo-950/80 text-indigo-400 border border-indigo-500/30 uppercase">
                Planner: {caseData.planner_mode}
              </span>
              {caseData.iterations_count > 1 && (
                <span className="text-xs font-mono px-2.5 py-1 rounded bg-amber-950/80 text-amber-400 border border-amber-500/30 flex items-center gap-1">
                  <RotateCcw className="h-3 w-3" />
                  {caseData.iterations_count} Loops Triggered
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Initialized: {new Date(caseData.created_at).toLocaleString()} • Status: <span className="text-emerald-400 font-semibold">{caseData.status}</span>
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">Deterministic Risk</span>
              <RiskBadge band={caseData.final_risk_band} score={caseData.final_risk_score} size="lg" />
            </div>
            <div className="text-right">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">Policy Decision</span>
              <DecisionBadge decision={caseData.final_decision} size="lg" />
            </div>
          </div>
        </div>

        {/* Deterministic Mathematical Rationale Callout */}
        {caseData.decision_rationale && (
          <div className="p-3.5 bg-background/80 rounded-xl border border-slate-800/80 text-xs font-mono text-slate-300 leading-relaxed">
            <strong className="text-indigo-400 font-bold block mb-1">DETERMINISTIC PYTHON RISK RATIONALE:</strong>
            {caseData.decision_rationale}
          </div>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('trail')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'trail' ? 'bg-indigo-600 text-white' : 'bg-surface text-slate-400 hover:text-slate-200'
          }`}
        >
          <Layers className="h-4 w-4" />
          <span>Full Agent Trail ({caseData.agent_trail_json?.length || 0})</span>
        </button>

        <button
          onClick={() => setActiveTab('subagents')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'subagents' ? 'bg-indigo-600 text-white' : 'bg-surface text-slate-400 hover:text-slate-200'
          }`}
        >
          <Network className="h-4 w-4" />
          <span>Sub-Agent Evidence & Graph</span>
        </button>

        <button
          onClick={() => setActiveTab('hypotheses')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'hypotheses' ? 'bg-indigo-600 text-white' : 'bg-surface text-slate-400 hover:text-slate-200'
          }`}
        >
          <BrainCircuit className="h-4 w-4" />
          <span>Hypotheses & Reasoning</span>
        </button>

        <button
          onClick={() => setActiveTab('sar')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'sar' ? 'bg-indigo-600 text-white' : 'bg-surface text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileSpreadsheet className="h-4 w-4" />
          <span>Drafted SAR Report</span>
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === 'audit' ? 'bg-indigo-600 text-white' : 'bg-surface text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldCheck className="h-4 w-4" />
          <span>Immutable Audit Logs ({caseData.audit_logs?.length || 0})</span>
        </button>
      </div>

      {/* Tab 1: Full Per-Agent Step Trail */}
      {activeTab === 'trail' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              Chronological Multi-Agent Execution Pipeline
            </h3>
            <span className="text-xs text-slate-400 font-mono">Click any step card to inspect JSON payload</span>
          </div>

          <div className="space-y-3">
            {caseData.agent_trail_json?.map((step, idx) => (
              <AgentTrailCard key={idx} step={step} stepIndex={idx} />
            ))}
          </div>
        </div>
      )}

      {/* Tab 2: Sub-Agent Evidence & Graph */}
      {activeTab === 'subagents' && (
        <div className="space-y-6">
          {/* Network Graph Section */}
          <div className="p-6 bg-surface rounded-2xl border border-slate-800 space-y-4">
            <div className="flex items-center gap-2.5">
              <Network className="h-5 w-5 text-indigo-400" />
              <div>
                <h3 className="text-base font-bold text-white">Graph Relationship Agent Findings</h3>
                <p className="text-xs text-slate-400">Multi-hop entity network traversal via NetworkX</p>
              </div>
            </div>
            <NetworkGraphView graphData={subagents.graph_data || {}} />
          </div>

          {/* Behavioral & Document Deep Dive */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-6 bg-surface rounded-2xl border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-indigo-400">
                <Activity className="h-4 w-4" />
                <h4 className="text-sm font-bold text-slate-100">Behavior Analysis Agent</h4>
              </div>
              <pre className="p-4 bg-background rounded-xl border border-slate-800 font-mono text-xs text-indigo-300 overflow-x-auto leading-relaxed">
                {JSON.stringify(subagents.behavior_data, null, 2)}
              </pre>
            </div>

            <div className="p-6 bg-surface rounded-2xl border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-indigo-400">
                <FileText className="h-4 w-4" />
                <h4 className="text-sm font-bold text-slate-100">Document Analysis Agent</h4>
              </div>
              <pre className="p-4 bg-background rounded-xl border border-slate-800 font-mono text-xs text-indigo-300 overflow-x-auto leading-relaxed">
                {JSON.stringify(subagents.document_data, null, 2)}
              </pre>
            </div>
          </div>

          {/* External Intelligence Section */}
          <div className="p-6 bg-surface rounded-2xl border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-indigo-400">
              <Globe2 className="h-4 w-4" />
              <h4 className="text-sm font-bold text-slate-100">External Intelligence Agent (Mocked PEP/Sanctions)</h4>
            </div>
            <pre className="p-4 bg-background rounded-xl border border-slate-800 font-mono text-xs text-indigo-300 overflow-x-auto leading-relaxed">
              {JSON.stringify(subagents.intelligence_data, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* Tab 3: Hypotheses & Forensic Reasoning */}
      {activeTab === 'hypotheses' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {caseData.hypotheses?.map((h) => (
              <div key={h.id} className="p-5 rounded-2xl bg-surface border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-indigo-400">{h.hypothesis_id}</span>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold ${
                    h.status === 'SUPPORTED' ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'
                  }`}>
                    {h.status} ({(h.probability * 100).toFixed(0)}%)
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-100">{h.title}</h4>
                <p className="text-xs text-slate-300 leading-relaxed">{h.description}</p>
              </div>
            ))}
          </div>

          <div className="p-6 bg-surface rounded-2xl border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-indigo-400">
              <BrainCircuit className="h-4 w-4" />
              <h4 className="text-sm font-bold text-slate-100">Analysis & Reasoning Agent Synthesis</h4>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed font-mono bg-background p-4 rounded-xl border border-slate-800">
              {reasoning.synthesis_summary || 'Reasoning synthesis completed.'}
            </p>
          </div>
        </div>
      )}

      {/* Tab 4: Drafted SAR Report */}
      {activeTab === 'sar' && (
        <SarReportViewer
          reportText={caseData.sar_report_text}
          sarJson={caseData.sar_narrative_json}
          caseId={caseData.case_id}
        />
      )}

      {/* Tab 5: Immutable Audit Logs */}
      {activeTab === 'audit' && (
        <div className="bg-surface border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
          <div className="p-4 border-b border-slate-800 bg-surface-light/20 flex items-center justify-between">
            <h4 className="text-xs font-mono uppercase tracking-wider text-slate-300 font-bold">
              Cryptographically Verified Audit Trails (SHA-256)
            </h4>
            <span className="text-[11px] font-mono text-emerald-400">Integrity: VERIFIED</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                  <th className="py-3 px-4">Actor</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Description</th>
                  <th className="py-3 px-4">Duration</th>
                  <th className="py-3 px-4">SHA-256 Digest</th>
                  <th className="py-3 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {caseData.audit_logs?.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/30">
                    <td className="py-3 px-4 text-indigo-400 font-semibold">{log.actor}</td>
                    <td className="py-3 px-4 text-slate-300">{log.action_type}</td>
                    <td className="py-3 px-4 text-slate-400 max-w-xs truncate font-sans text-xs">{log.description}</td>
                    <td className="py-3 px-4 text-slate-400">{log.execution_time_ms}ms</td>
                    <td className="py-3 px-4 text-slate-500 truncate max-w-[120px]" title={log.verification_hash}>
                      {log.verification_hash}
                    </td>
                    <td className="py-3 px-4 text-slate-500">{new Date(log.timestamp).toLocaleTimeString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Human Feedback Modal */}
      <FeedbackModal
        caseId={caseData.case_id}
        currentDecision={caseData.final_decision}
        isOpen={feedbackOpen}
        onClose={() => setFeedbackOpen(false)}
        onSubmitted={fetchDetail}
      />
    </div>
  );
};
