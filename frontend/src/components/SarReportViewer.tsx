import React, { useState } from 'react';
import {
  FileText, Copy, Check, Download, AlertTriangle, ShieldCheck, ShieldAlert, CheckCircle2, XCircle, Ban,
} from 'lucide-react';

interface SarReportViewerProps {
  reportText?: string;
  sarJson?: Record<string, any>;
  caseId: string;
}

const TIER_LABEL: Record<string, string> = {
  TIER_1_URGENT: 'Tier 1 · Urgent',
  TIER_2_PRIORITY: 'Tier 2 · Priority',
  TIER_3_ROUTINE: 'Tier 3 · Routine',
};

export const SarReportViewer: React.FC<SarReportViewerProps> = ({ reportText, sarJson, caseId }) => {
  const [copied, setCopied] = useState(false);
  const [showRaw, setShowRaw] = useState(false);

  const handleCopy = () => {
    if (reportText) {
      navigator.clipboard.writeText(reportText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (reportText) {
      const element = document.createElement('a');
      const file = new Blob([reportText], { type: 'text/markdown' });
      element.href = URL.createObjectURL(file);
      element.download = `STR_${caseId}_DRAFT.md`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    }
  };

  if (!reportText) {
    return (
      <div className="p-8 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
        No report generated for this case.
      </div>
    );
  }

  const decision = sarJson?.filing_decision;
  const verification = sarJson?.verification;
  const claims: any[] = sarJson?.claims ?? [];
  const isStr = sarJson?.report_type === 'STR_DRAFT';
  const blocked = verification?.approval_status === 'BLOCKED_UNVERIFIED_CLAIMS';
  const completeness = verification?.completeness;

  return (
    <div className="space-y-4">
      {/* Decision + verification summary */}
      {decision && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className={`p-4 rounded-xl border ${isStr ? 'bg-rose-950/30 border-rose-500/40' : 'bg-emerald-950/30 border-emerald-500/40'}`}>
            <div className="text-[11px] uppercase tracking-wide text-slate-400">Filing decision</div>
            <div className={`mt-1 text-lg font-bold ${isStr ? 'text-rose-300' : 'text-emerald-300'}`}>
              {isStr ? 'File STR to FIU-IND' : 'Do not file — memo recorded'}
            </div>
            {decision.tier && <div className="text-xs text-rose-200 mt-0.5">{TIER_LABEL[decision.tier] ?? decision.tier}</div>}
          </div>
          <div className={`p-4 rounded-xl border ${blocked ? 'bg-amber-950/30 border-amber-500/40' : 'bg-emerald-950/30 border-emerald-500/40'}`}>
            <div className="text-[11px] uppercase tracking-wide text-slate-400">Fact check</div>
            <div className="mt-1 flex items-center gap-2 text-lg font-bold text-slate-100">
              {blocked ? <ShieldAlert className="h-5 w-5 text-amber-400" /> : <ShieldCheck className="h-5 w-5 text-emerald-400" />}
              {verification?.verified_claims}/{verification?.total_claims} claims verified
            </div>
            <div className="text-xs text-slate-400 mt-0.5">{blocked ? 'Approval blocked until fixed' : 'Ready for Principal Officer review'}</div>
          </div>
          <div className="p-4 rounded-xl border bg-surface border-slate-800">
            <div className="text-[11px] uppercase tracking-wide text-slate-400">Completeness (5W1H)</div>
            <div className="mt-1 text-lg font-bold text-slate-100">{Math.round((completeness?.score ?? 0) * 100)}%</div>
            <div className="flex flex-wrap gap-1 mt-1">
              {completeness &&
                Object.entries(completeness.checks as Record<string, boolean>).map(([k, ok]) => (
                  <span key={k} className={`text-[10px] px-1.5 py-0.5 rounded ${ok ? 'bg-emerald-900/50 text-emerald-300' : 'bg-rose-900/50 text-rose-300'}`}>
                    {k}
                  </span>
                ))}
            </div>
          </div>
        </div>
      )}

      {/* Reasons: grounds of suspicion or reason for not filing */}
      {decision?.reasons?.length > 0 && (
        <div className="p-4 rounded-xl border border-slate-800 bg-surface">
          <h4 className="text-xs font-semibold text-slate-300 mb-2">{isStr ? 'Grounds of suspicion' : 'Why no STR is being filed'}</h4>
          <ul className="space-y-1 text-xs text-slate-300 list-disc pl-4">
            {decision.reasons.map((r: string, i: number) => <li key={i}>{r}</li>)}
          </ul>
          {decision.recommended_action && <p className="text-xs text-indigo-300 mt-2">→ {decision.recommended_action}</p>}
        </div>
      )}

      {/* Evidence-linked claims */}
      {claims.length > 0 && (
        <div className="p-4 rounded-xl border border-slate-800 bg-surface">
          <h4 className="text-xs font-semibold text-slate-300 mb-1">Evidence-linked facts</h4>
          <p className="text-[11px] text-slate-500 mb-3">Each line was re-computed from the ledger using only its linked records. The AI cannot add a number that the data does not support.</p>
          <ul className="space-y-2">
            {claims.map((c) => {
              const ok = c.status === 'VERIFIED';
              return (
                <li key={c.claim_id} className={`p-2.5 rounded-lg border text-xs ${ok ? 'border-emerald-800/60 bg-emerald-950/20' : 'border-rose-700/60 bg-rose-950/30'}`}>
                  <div className="flex items-start gap-2">
                    {ok ? <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" /> : <XCircle className="h-4 w-4 text-rose-400 shrink-0" />}
                    <div className="flex-1">
                      <div className="text-slate-100">{c.text}</div>
                      <div className="text-[10px] text-slate-500 mt-0.5">
                        {c.category?.toUpperCase()} · {c.evidence_ids?.length ?? 0} linked record(s) · {c.claim_id}
                      </div>
                      {!ok && (c.verification_notes ?? []).map((n: string, i: number) => (
                        <div key={i} className="text-[11px] text-rose-300 mt-1">⚠ {n}</div>
                      ))}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      {/* Compliance banner */}
      <div className="p-3.5 bg-amber-950/40 border border-amber-500/40 rounded-xl flex items-start gap-3 text-amber-200 text-xs">
        {blocked ? <Ban className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" /> : <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />}
        <div>
          <span className="font-semibold text-amber-300">DRAFT FOR HUMAN SIGN-OFF: </span>
          Under PMLA, the Principal Officer decides whether to file and authorises the STR content.
          {blocked && ' Approval is blocked because some claims are not supported by the ledger.'}
        </div>
      </div>

      {/* Report actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-indigo-400" />
          <h4 className="text-sm font-semibold text-slate-200">{isStr ? 'FIU-IND STR Draft' : 'Alert Closure Memo'}</h4>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowRaw(!showRaw)} className="px-3 py-1.5 rounded-lg bg-surface border border-slate-700 hover:border-slate-600 text-slate-300 text-xs font-medium">
            {showRaw ? 'Hide full text' : 'Show full text'}
          </button>
          <button onClick={handleCopy} className="px-3 py-1.5 rounded-lg bg-surface border border-slate-700 hover:border-slate-600 text-slate-300 text-xs font-medium flex items-center gap-1.5 transition-colors">
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? 'Copied' : 'Copy'}
          </button>
          <button onClick={handleDownload} className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors">
            <Download className="h-3.5 w-3.5" />
            Download (.md)
          </button>
        </div>
      </div>

      {(showRaw || !decision) && (
        <div className="p-6 bg-surface rounded-xl border border-slate-800 text-slate-200 font-mono text-xs leading-relaxed overflow-x-auto whitespace-pre-wrap">
          {reportText}
        </div>
      )}
    </div>
  );
};
