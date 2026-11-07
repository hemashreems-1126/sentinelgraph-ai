import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, FolderSearch, ChevronRight, ShieldCheck, ShieldAlert, RefreshCw } from 'lucide-react';
import { apiClient } from '../api/client';
import { InvestigationCaseSummary } from '../types';
import { FilingBadge } from '../components/FilingBadge';
import { REVIEW_LABEL, urgencyRank } from '../labels';

/** The analyst's inbox: most urgent first, one line per case saying who, what and why. */
export const InvestigationsPage: React.FC = () => {
  const navigate = useNavigate();
  const [cases, setCases] = useState<InvestigationCaseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [decisionFilter, setDecisionFilter] = useState('');
  const [reviewFilter, setReviewFilter] = useState('');
  const [search, setSearch] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      setCases(await apiClient.getInvestigations({ limit: 200 }));
    } catch (err) {
      window.alert(`Could not load cases. ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const q = search.toLowerCase();
  const shown = cases
    .filter((c) => !decisionFilter || c.filing_decision === decisionFilter)
    .filter((c) => !reviewFilter || (reviewFilter === 'todo' ? !c.analyst_review : !!c.analyst_review))
    .filter((c) => !q || [c.subject_name, c.case_id, c.alert_id, c.headline].some((v) => (v || '').toLowerCase().includes(q)))
    .sort((a, b) =>
      (a.analyst_review ? 1 : 0) - (b.analyst_review ? 1 : 0) ||
      urgencyRank(a.filing_decision, a.filing_tier) - urgencyRank(b.filing_decision, b.filing_tier) ||
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );
  const todo = cases.filter((c) => !c.analyst_review).length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Cases</h1>
          <p className="text-sm text-slate-400 mt-1">
            {todo} waiting for your review · most urgent first. Open a case to approve or disagree.
          </p>
        </div>
        <button onClick={load} className="self-start md:self-auto px-3 py-2 rounded-xl bg-surface border border-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1.5">
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </button>
      </div>

      <div className="p-3 rounded-2xl bg-surface border border-slate-800 flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[220px] relative">
          <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by customer, case or reason…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-background border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          />
        </div>
        <select value={decisionFilter} onChange={(e) => setDecisionFilter(e.target.value)}
          className="px-3 py-2 bg-background border border-slate-800 rounded-xl text-xs text-slate-300">
          <option value="">All recommendations</option>
          <option value="FILE_STR">File STR</option>
          <option value="NO_FILE">Don't file</option>
        </select>
        <select value={reviewFilter} onChange={(e) => setReviewFilter(e.target.value)}
          className="px-3 py-2 bg-background border border-slate-800 rounded-xl text-xs text-slate-300">
          <option value="">All cases</option>
          <option value="todo">Needs my review</option>
          <option value="done">Already reviewed</option>
        </select>
      </div>

      <div className="bg-surface border border-slate-800 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading cases…</div>
        ) : shown.length === 0 ? (
          <div className="p-12 text-center text-slate-500 space-y-3">
            <FolderSearch className="h-8 w-8 mx-auto text-slate-600" />
            <p className="text-sm">No cases here yet. Start one from the Alerts page.</p>
            <button onClick={() => navigate('/alerts')} className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold">
              Go to Alerts
            </button>
          </div>
        ) : (
          <ul className="divide-y divide-slate-800/70">
            {shown.map((c) => {
              const blocked = c.report_status === 'BLOCKED_UNVERIFIED_CLAIMS';
              return (
                <li key={c.id}>
                  <button
                    onClick={() => navigate(`/investigations/${c.case_id}`)}
                    className="w-full text-left px-5 py-4 hover:bg-slate-800/40 transition-colors flex items-center gap-4"
                  >
                    <div className="flex-1 min-w-0 space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-bold text-slate-100">{c.subject_name || c.alert_id}</span>
                        <FilingBadge decision={c.filing_decision} tier={c.filing_tier} />
                        {c.analyst_review ? (
                          <span className="text-[11px] px-2 py-0.5 rounded-md bg-indigo-950/70 border border-indigo-500/30 text-indigo-300">
                            {REVIEW_LABEL[c.analyst_review] ?? c.analyst_review}
                          </span>
                        ) : (
                          <span className="text-[11px] px-2 py-0.5 rounded-md bg-amber-950/60 border border-amber-500/30 text-amber-300">Needs review</span>
                        )}
                      </div>
                      <p className="text-sm text-slate-400 truncate">{c.headline || 'No summary available.'}</p>
                    </div>
                    <div className="hidden sm:flex flex-col items-end gap-1 text-[11px] text-slate-500 shrink-0">
                      <span className={`inline-flex items-center gap-1 ${blocked ? 'text-amber-300' : 'text-emerald-400'}`}>
                        {blocked ? <ShieldAlert className="h-3.5 w-3.5" /> : <ShieldCheck className="h-3.5 w-3.5" />}
                        {blocked ? 'Facts need fixing' : 'Facts verified'}
                      </span>
                      <span>{new Date(c.created_at).toLocaleString()}</span>
                    </div>
                    <ChevronRight className="h-4 w-4 text-slate-500 shrink-0" />
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
};
