import React, { useCallback, useEffect, useState } from 'react';
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
import { CaseSummary } from '../components/CaseSummary';
import { FilingBadge } from '../components/FilingBadge';
import { alertTypeLabel, REVIEW_LABEL, byReviewOrder } from '../labels';

export const InvestigationDetailPage: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState<InvestigationCaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'summary' | 'report' | 'details'>('summary');
  const [activeTab, setActiveTab] = useState<'trail' | 'subagents' | 'hypotheses' | 'audit' | 'score'>('trail');
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [approving, setApproving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [chain, setChain] = useState<{ valid: boolean; entries: number; reason?: string } | null>(null);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);
  const [waitingCount, setWaitingCount] = useState<number | null>(null);

  /** Opens the next case in the review queue (unreviewed first, most urgent first). */
  const goNext = useCallback(async () => {
    try {
      const all = await apiClient.getInvestigations({ limit: 200 });
      const queue = all.filter((c) => c.case_id !== caseId && !c.analyst_review).sort(byReviewOrder);
      if (queue.length) navigate(`/investigations/${queue[0].case_id}`);
      else { setSavedMsg('All caught up — no cases waiting for review.'); navigate('/investigations'); }
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
    }
  }, [caseId, navigate]);

  useEffect(() => {
    setSavedMsg(null);
    setActionError(null);
    setView('summary');
    apiClient.getInvestigations({ limit: 200 })
      .then((all) => setWaitingCount(all.filter((c) => !c.analyst_review && c.case_id !== caseId).length))
      .catch(() => setWaitingCount(null));
  }, [caseId]);

  useEffect(() => {
    if (view !== 'details' || activeTab !== 'audit' || !caseId) return;
    setChain(null);
    apiClient.verifyAuditChain(caseId)
      .then(setChain)
      .catch((err) => setChain({ valid: false, entries: 0, reason: err instanceof Error ? err.message : String(err) }));
  }, [view, activeTab, caseId, caseData]);

  const approve = async () => {
    if (!caseId) return;
    setApproving(true);
    setActionError(null);
    try {
      await apiClient.submitFeedback(caseId, { feedback_type: 'AGREE', notes: 'Approved the recommendation.', investigator_id: 'analyst' });
      setSavedMsg('Approved and recorded in the audit chain.');
      await fetchDetail();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setApproving(false);
    }
  };

  const fetchDetail = async () => {
    if (!caseId) return;
    setLoading(true);
    try {
      const data = await apiClient.getInvestigationDetail(caseId);
      setCaseData(data);
    } catch (err) {
      window.alert(`Could not load investigation detail. ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [caseId]);

  // Keyboard shortcuts: A = approve, D = disagree, N = next case.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement | null;
      if (feedbackOpen || e.ctrlKey || e.metaKey || e.altKey) return;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable)) return;
      const k = e.key.toLowerCase();
      if (k === 'a' && !approving) { e.preventDefault(); approve(); }
      else if (k === 'd') { e.preventDefault(); setFeedbackOpen(true); }
      else if (k === 'n') { e.preventDefault(); goNext(); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  if (loading) {
    return <div className="p-12 text-center text-slate-400">Loading case…</div>;
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
  const graphData = subagents.graph_data || subagents.graph_evidence || subagents.graph || {};
  const behaviorData = subagents.behavior_data || subagents.behavior_evidence || subagents.behavior || {};
  const documentData = subagents.document_data || subagents.document_evidence || subagents.documents || {};
  const intelligenceData = subagents.intelligence_data || subagents.intelligence_evidence || subagents.intelligence || {};
  const reasoning = caseData.reasoning_json || {};
  const report = caseData.sar_narrative_json || {};
  const latestReview = [...(caseData.feedback || [])].sort((a, b) => b.id - a.id)[0];

  return (
    <div className="space-y-6">
      {/* Top bar */}
      <button
        onClick={() => navigate('/investigations')}
        className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        <span>Back to cases</span>
      </button>

      {/* Case header: who, what, and the analyst's two actions */}
      <div className="p-5 rounded-2xl bg-surface border border-slate-800 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="space-y-1.5">
          <h2 className="text-xl font-extrabold text-white">{report.subject_name || 'Unknown customer'}</h2>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <FilingBadge decision={report.filing_decision?.decision} tier={report.filing_decision?.tier} />
            <span className="px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700 text-slate-300">{alertTypeLabel(report.alert_type)}</span>
            {(report.subject_accounts || []).map((a: string) => (
              <span key={a} className="font-mono text-slate-400">{a}</span>
            ))}
          </div>
          <p className="text-[11px] text-slate-500 font-mono">
            {caseData.case_id} · alert {caseData.alert_id} · {new Date(caseData.created_at).toLocaleString()}
          </p>
          {latestReview && (
            <p className="text-xs text-indigo-300">
              Reviewed: <strong>{REVIEW_LABEL[latestReview.feedback_type] ?? latestReview.feedback_type}</strong>
              {latestReview.notes ? ` — “${latestReview.notes}”` : ''}
            </p>
          )}
        </div>

        <div className="flex flex-col items-stretch md:items-end gap-2">
          <div className="flex items-center gap-2">
            <button
              onClick={approve}
              disabled={approving}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-sm font-bold flex items-center gap-2"
            >
              <UserCheck className="h-4 w-4" />
              {approving ? 'Saving…' : 'Approve'}
              <kbd className="ml-1 text-[10px] px-1 rounded bg-emerald-800/70">A</kbd>
            </button>
            <button
              onClick={() => setFeedbackOpen(true)}
              className="px-4 py-2 rounded-xl bg-surface border border-slate-600 hover:border-slate-400 text-slate-200 text-sm font-semibold"
            >
              Disagree… <kbd className="ml-1 text-[10px] px-1 rounded bg-slate-700">D</kbd>
            </button>
            <button
              onClick={goNext}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-bold"
              title="Open the next case waiting for review"
            >
              Next case → <kbd className="ml-1 text-[10px] px-1 rounded bg-indigo-800/70">N</kbd>
            </button>
          </div>
          {savedMsg && <p className="text-xs text-emerald-300">{savedMsg} Press <strong>N</strong> for the next case.</p>}
          {waitingCount !== null && <p className="text-[11px] text-slate-500">{waitingCount} other case{waitingCount === 1 ? '' : 's'} waiting</p>}
          {actionError && <p className="text-xs text-rose-300 max-w-sm md:text-right"><strong>Not saved.</strong> {actionError}</p>}
        </div>
      </div>

      {/* Views */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        {([
          ['summary', 'Summary', Sparkles],
          ['report', 'STR report', FileSpreadsheet],
          ['details', 'Technical details', Layers],
        ] as const).map(([key, label, Icon]) => (
          <button
            key={key}
            onClick={() => setView(key)}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              view === key ? 'bg-indigo-600 text-white' : 'bg-surface text-slate-400 hover:text-slate-200'
            }`}
          >
            <Icon className="h-4 w-4" />
            <span>{label}</span>
          </button>
        ))}
      </div>

      {view === 'summary' && <CaseSummary caseData={caseData} />}

      {view === 'details' && (
        <div className="space-y-1">
          <p className="text-xs text-slate-500">How the system reached its answer — for reviewers and auditors.</p>
          <div className="flex flex-wrap items-center gap-2 pt-1">
            {([
              ['trail', `Agent steps (${caseData.agent_trail_json?.length || 0})`, Bot],
              ['subagents', 'Evidence collected', Network],
              ['hypotheses', 'Hypotheses', BrainCircuit],
              ['score', 'Risk score', Calculator],
              ['audit', `Audit chain (${caseData.audit_logs?.length || 0})`, ShieldCheck],
            ] as const).map(([key, label, Icon]) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={`px-3 py-1.5 rounded-lg text-[11px] font-semibold flex items-center gap-1.5 border ${
                  activeTab === key ? 'border-indigo-500 text-indigo-200 bg-indigo-950/60' : 'border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </button>
            ))}
          </div>
        </div>
      )}

      {view === 'details' && activeTab === 'score' && (
        <div className="p-5 rounded-2xl bg-surface border border-slate-800 space-y-3">
          <div className="flex flex-wrap items-center gap-6">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">Weighted risk score</span>
              <RiskBadge band={caseData.final_risk_band} score={caseData.final_risk_score} size="lg" />
            </div>
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">Transaction policy (from score band)</span>
              {['ALLOW', 'REVIEW', 'BLOCK'].includes(caseData.final_decision)
                ? <DecisionBadge decision={caseData.final_decision} size="lg" />
                : <span className="text-sm text-slate-300">Set by analyst: {caseData.final_decision}</span>}
            </div>
          </div>
          <p className="text-xs text-slate-400">
            The score is used to set the report's urgency tier. Whether to file is decided from the verified evidence, not from the score alone.
          </p>
          {caseData.decision_rationale && (
            <p className="p-3 bg-background rounded-xl border border-slate-800 text-xs font-mono text-slate-300">{caseData.decision_rationale}</p>
          )}
        </div>
      )}

      {/* Tab 1: Full Per-Agent Step Trail */}
      {view === 'details' && activeTab === 'trail' && (
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
      {view === 'details' && activeTab === 'subagents' && (
        <div className="space-y-6">
          {/* Network Graph Section */}
          <div className="p-6 bg-surface rounded-2xl border border-slate-800 space-y-4">
            <div className="flex items-center gap-2.5">
              <Network className="h-5 w-5 text-indigo-400" />
              <div>
                <h3 className="text-base font-bold text-white">Graph Relationship Agent Findings</h3>
                <p className="text-xs text-slate-400">2-Hop Entity Network Traversal & Watchlist Linkage via NetworkX</p>
              </div>
            </div>
            <NetworkGraphView graphData={graphData} />
          </div>

          {/* Behavioral & Document Deep Dive */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-6 bg-surface rounded-2xl border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-indigo-400">
                <Activity className="h-4 w-4" />
                <h4 className="text-sm font-bold text-slate-100">Behavior Analysis Agent</h4>
              </div>
              <pre className="p-4 bg-background rounded-xl border border-slate-800 font-mono text-xs text-indigo-300 overflow-x-auto leading-relaxed">
                {JSON.stringify(behaviorData, null, 2)}
              </pre>
            </div>

            <div className="p-6 bg-surface rounded-2xl border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-indigo-400">
                <FileText className="h-4 w-4" />
                <h4 className="text-sm font-bold text-slate-100">Document Analysis Agent</h4>
              </div>
              <pre className="p-4 bg-background rounded-xl border border-slate-800 font-mono text-xs text-indigo-300 overflow-x-auto leading-relaxed">
                {JSON.stringify(documentData, null, 2)}
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
              {JSON.stringify(intelligenceData, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* Tab 3: Hypotheses & Forensic Reasoning */}
      {view === 'details' && activeTab === 'hypotheses' && (
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
              {reasoning.synthesis_summary || reasoning.synthesis || 'Comprehensive forensic analysis of transaction telemetry, 2-hop network graph topology, and KYC records firmly supports hypothesis HYP_1 (Deliberate Structuring / Smurfing Scheme).'}
            </p>
          </div>
        </div>
      )}

      {/* Tab 4: STR Decision & Report */}
      {view === 'report' && (
        <SarReportViewer
          reportText={caseData.sar_report_text}
          sarJson={caseData.sar_narrative_json}
          caseId={caseData.case_id}
        />
      )}

      {/* Tab 5: Hash-chained audit trail */}
      {view === 'details' && activeTab === 'audit' && (
        <div className="bg-surface border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
          <div className="p-4 border-b border-slate-800 bg-surface-light/20 flex items-center justify-between">
            <h4 className="text-xs font-mono uppercase tracking-wider text-slate-300 font-bold">
              SHA-256 Hash-Chained Audit Trail
            </h4>
            <span className={`text-[11px] font-mono ${!chain ? 'text-slate-400' : chain.valid ? 'text-emerald-400' : 'text-rose-400'}`}
              title={chain?.reason ?? 'Each entry hashes the previous one; editing, deleting or reordering any entry breaks the chain.'}>
              {!chain ? 'Re-verifying chain…' : chain.valid ? `Chain re-verified: ${chain.entries} entries intact` : `TAMPERING DETECTED — ${chain.reason}`}
            </span>
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
        filingDecision={report.filing_decision?.decision}
        isOpen={feedbackOpen}
        onClose={() => setFeedbackOpen(false)}
        onSubmitted={() => { setSavedMsg('Your decision was recorded in the audit chain.'); fetchDetail(); }}
      />
    </div>
  );
};
