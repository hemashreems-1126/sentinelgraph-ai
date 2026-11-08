import React from 'react';
import { CheckCircle2, XCircle, FileWarning, FileCheck2, ShieldCheck, ShieldAlert } from 'lucide-react';
import { InvestigationCaseDetail } from '../types';
import { NetworkGraphView } from './NetworkGraphView';
import { TIER_LABEL } from '../labels';

/** The analyst's first view of a case: the decision, why, the verified facts, and the money flow. */
export const CaseSummary: React.FC<{ caseData: InvestigationCaseDetail }> = ({ caseData }) => {
  const report = caseData.sar_narrative_json || {};
  const decision = report.filing_decision || {};
  const verification = report.verification || {};
  const claims: any[] = report.claims || [];
  const claimStatus: Record<string, string> = Object.fromEntries(claims.map((c) => [c.claim_id, c.status]));
  const isStr = decision.decision === 'FILE_STR';
  const blocked = verification.approval_status === 'BLOCKED_UNVERIFIED_CLAIMS';
  const grounds: any[] = report.grounds_of_suspicion || [];
  const graphData = caseData.subagent_evidence_json?.graph_data || {};

  if (!decision.decision) {
    return (
      <div className="p-6 rounded-2xl bg-surface border border-slate-800 text-sm text-slate-400">
        This case was created by an older version and has no summary. Open “Report” or “Technical details”.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* The answer */}
      <div className={`p-5 rounded-2xl border ${isStr ? 'bg-rose-950/30 border-rose-500/40' : 'bg-emerald-950/30 border-emerald-500/40'}`}>
        <div className="flex items-start gap-3">
          {isStr ? <FileWarning className="h-6 w-6 text-rose-300 shrink-0" /> : <FileCheck2 className="h-6 w-6 text-emerald-300 shrink-0" />}
          <div className="space-y-1">
            <div className={`text-lg font-extrabold ${isStr ? 'text-rose-200' : 'text-emerald-200'}`}>
              {isStr ? 'Recommendation: file an STR with FIU-IND' : 'Recommendation: do not file — close with a memo'}
              {decision.tier && <span className="ml-2 text-sm font-bold text-rose-300">({TIER_LABEL[decision.tier] ?? decision.tier})</span>}
            </div>
            {decision.recommended_action && <p className="text-sm text-slate-300">{decision.recommended_action}</p>}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Why */}
        <div className="p-5 rounded-2xl bg-surface border border-slate-800 space-y-3">
          <h3 className="text-sm font-bold text-white">{isStr ? 'Why this looks suspicious' : 'Why no report is needed'}</h3>
          <ul className="space-y-2">
            {isStr
              ? grounds.map((g, i) => {
                  const ok = !g.claim_id || claimStatus[g.claim_id] === 'VERIFIED';
                  return (
                    <li key={i} className="flex gap-2 text-sm text-slate-200">
                      {ok ? <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" /> : <XCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />}
                      <span>{g.description}</span>
                    </li>
                  );
                })
              : (decision.reasons || []).map((r: string, i: number) => (
                  <li key={i} className="flex gap-2 text-sm text-slate-200">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{r}</span>
                  </li>
                ))}
          </ul>
        </div>

        {/* Facts */}
        <div className="p-5 rounded-2xl bg-surface border border-slate-800 space-y-3">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-bold text-white">Facts, checked against the transactions</h3>
            <span className={`inline-flex items-center gap-1 text-xs font-semibold ${blocked ? 'text-amber-300' : 'text-emerald-300'}`}>
              {blocked ? <ShieldAlert className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
              {verification.verified_claims}/{verification.total_claims} verified
            </span>
          </div>
          <ul className="space-y-2">
            {claims.map((c) => (
              <li key={c.claim_id} className="flex gap-2 text-sm text-slate-300">
                {c.status === 'VERIFIED'
                  ? <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                  : <XCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />}
                <span>
                  {c.text}
                  {c.status !== 'VERIFIED' && (c.verification_notes || []).map((n: string, i: number) => (
                    <span key={i} className="block text-xs text-rose-300">{n}</span>
                  ))}
                </span>
              </li>
            ))}
          </ul>
          {blocked && <p className="text-xs text-amber-300">Some facts are not supported by the data, so this report cannot be approved until they are fixed.</p>}
        </div>
      </div>

      {/* Money flow */}
      {graphData.nodes?.length > 0 && (
        <div className="p-5 rounded-2xl bg-surface border border-slate-800 space-y-3">
          <h3 className="text-sm font-bold text-white">Where the money went</h3>
          <NetworkGraphView graphData={graphData} />
        </div>
      )}
    </div>
  );
};
