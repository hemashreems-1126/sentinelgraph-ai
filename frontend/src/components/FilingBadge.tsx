import React from 'react';
import { FileWarning, FileCheck2, HelpCircle } from 'lucide-react';

const TIER: Record<string, string> = { TIER_1_URGENT: 'Tier 1', TIER_2_PRIORITY: 'Tier 2', TIER_3_ROUTINE: 'Tier 3' };

/** Shows the evidence-based outcome of an investigation: file an STR (with tier) or close with a memo. */
export const FilingBadge: React.FC<{ decision?: string | null; tier?: string | null }> = ({ decision, tier }) => {
  if (decision === 'FILE_STR') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[11px] font-bold bg-rose-500/10 text-rose-300 border-rose-500/30">
        <FileWarning className="h-3 w-3" /> FILE STR{tier ? ` · ${TIER[tier] ?? tier}` : ''}
      </span>
    );
  }
  if (decision === 'NO_FILE') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[11px] font-bold bg-emerald-500/10 text-emerald-300 border-emerald-500/30">
        <FileCheck2 className="h-3 w-3" /> NO STR · memo
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[11px] bg-slate-800 text-slate-400 border-slate-700">
      <HelpCircle className="h-3 w-3" /> —
    </span>
  );
};
