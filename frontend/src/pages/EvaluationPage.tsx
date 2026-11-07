import React, { useEffect, useState } from 'react';
import { Play, Radar, FileCheck2, ShieldCheck, Info } from 'lucide-react';
import { apiClient } from '../api/client';
import { EvaluationMetric } from '../types';

const pct = (x?: number) => (x === undefined || x === null ? '—' : `${(x * 100).toFixed(1)}%`);
const label = (s: string) => s.replace(/_/g, ' ').toLowerCase().replace(/^\w/, (c) => c.toUpperCase());

const Stat: React.FC<{ title: string; value: string; hint?: string; tone?: 'good' | 'warn' | 'neutral' }> = ({ title, value, hint, tone = 'neutral' }) => (
  <div className="p-4 rounded-xl bg-surface border border-slate-800">
    <div className="text-[11px] uppercase tracking-wide text-slate-400">{title}</div>
    <div className={`mt-1 text-2xl font-extrabold ${tone === 'good' ? 'text-emerald-300' : tone === 'warn' ? 'text-amber-300' : 'text-slate-100'}`}>{value}</div>
    {hint && <div className="text-[11px] text-slate-500 mt-1 leading-snug">{hint}</div>}
  </div>
);

const StageHeader: React.FC<{ n: number; icon: React.ReactNode; title: string; question: string }> = ({ n, icon, title, question }) => (
  <div className="flex items-start gap-3">
    <div className="p-2 rounded-lg bg-indigo-950/80 text-indigo-400 border border-indigo-500/30">{icon}</div>
    <div>
      <h2 className="text-base font-bold text-slate-100">Stage {n} · {title}</h2>
      <p className="text-xs text-slate-400">{question}</p>
    </div>
  </div>
);

export const EvaluationPage: React.FC = () => {
  const [ev, setEv] = useState<EvaluationMetric | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    apiClient.getLatestEvaluation()
      .then(setEv)
      .catch((err) => window.alert(`Could not load evaluation. ${err instanceof Error ? err.message : String(err)}`))
      .finally(() => setLoading(false));
  }, []);

  const run = async () => {
    setRunning(true);
    try {
      setEv(await apiClient.triggerEvaluation('TEST', 42, 120));
    } catch (err) {
      window.alert(`Could not run evaluation. ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setRunning(false);
    }
  };

  const m = ev?.metrics_json;

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Evaluation</h1>
          <p className="text-sm text-slate-400 mt-1 max-w-3xl">
            Every number below comes from actually running detection, the multi-agent investigation, the filing
            decision and the fact checker on held-out alerts — nothing is estimated.
          </p>
        </div>
        <button onClick={run} disabled={running}
          className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-2 self-start md:self-auto">
          <Play className={`h-3.5 w-3.5 fill-current ${running ? 'animate-pulse' : ''}`} />
          {running ? 'Investigating 120 alerts… (about a minute)' : 'Run evaluation (120 alerts)'}
        </button>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-400">Loading evaluation…</div>
      ) : !m ? (
        <div className="p-12 text-center text-slate-500">No staged evaluation yet. Click “Run evaluation”.</div>
      ) : (
        <>
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 text-xs text-slate-300 flex gap-3">
            <Info className="h-4 w-4 text-indigo-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <div><strong>Dataset:</strong> {m.dataset} · <strong>Split:</strong> held-out {m.split} alerts · run {ev?.run_id} · {m.runtime_seconds}s</div>
              <div><strong>Ground truth:</strong> {m.ground_truth}</div>
              <div className="text-slate-400">The synthetic data includes legitimate look-alikes (shops, payroll, rent splits, cash businesses) so that a rule cannot look perfect. Run <code>python run_eval.py --ibm …</code> to evaluate on the public IBM AML dataset instead.</div>
            </div>
          </div>

          {/* Stage 1 */}
          <section className="space-y-4">
            <StageHeader n={1} icon={<Radar className="h-5 w-5" />} title="Detection"
              question="How noisy are the alerts raised by the rules and the Isolation Forest?" />
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              <Stat title="Alerts evaluated" value={String(m.detection.alerts_evaluated)} />
              <Stat title="Alert precision" value={pct(m.detection.alert_precision)} hint="Share of alerts whose subject really is a criminal-controlled account" />
              <Stat title="Criminal accounts alerted" value={pct(m.detection.controlled_account_coverage)} hint={`of ${m.detection.controlled_accounts} controlled accounts got at least one alert`} />
            </div>
            <div className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-xs">
                <thead className="bg-slate-900 text-slate-400"><tr><th className="text-left p-2.5">Alert type</th><th className="text-right p-2.5">Alerts</th><th className="text-right p-2.5">Truly suspicious</th><th className="text-right p-2.5">Precision</th></tr></thead>
                <tbody>
                  {Object.entries(m.detection.by_alert_type).map(([k, v]) => (
                    <tr key={k} className="border-t border-slate-800 text-slate-300">
                      <td className="p-2.5">{label(k)}</td><td className="p-2.5 text-right">{v.alerts}</td>
                      <td className="p-2.5 text-right">{v.true_suspicious}</td><td className="p-2.5 text-right">{pct(v.precision)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Stage 2 */}
          <section className="space-y-4">
            <StageHeader n={2} icon={<FileCheck2 className="h-5 w-5" />} title="Filing decision"
              question="After investigation, does SentinelGraph file STRs for the right alerts and close the rest with a documented reason?" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Stat title="Precision" value={pct(m.filing.precision)} tone="good" hint="Filed STRs that were truly suspicious" />
              <Stat title="Recall" value={pct(m.filing.recall)} tone="good" hint="Truly suspicious alerts that were filed" />
              <Stat title="F1" value={m.filing.f1.toFixed(3)} />
              <Stat title="Alerts closed with memo" value={pct(m.filing.alert_reduction_rate)} tone="good" hint="Analyst workload removed, each with a written reason" />
              <Stat title="Look-alikes wrongly filed" value={pct(m.filing.hard_negative_false_file_rate)} tone="warn" hint={`of ${m.filing.hard_negative_cases} legitimate shops / payroll / rent splits / cash businesses`} />
              <Stat title="Risk-score ROC-AUC" value={m.filing.risk_score_roc_auc.toFixed(3)} tone="warn" hint="The weighted score alone separates poorly — the evidence-based decision does the work" />
              <Stat title="Cases investigated" value={String(m.filing.cases_investigated)} />
              <Stat title="Avg time per case" value={`${m.filing.avg_seconds_per_case.toFixed(2)}s`} />
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="rounded-xl border border-slate-800 p-4 bg-surface">
                <div className="text-xs font-semibold text-slate-300 mb-3">Confusion matrix (filing)</div>
                <div className="grid grid-cols-3 gap-2 text-xs text-center">
                  <div /><div className="text-slate-400">Filed</div><div className="text-slate-400">Not filed</div>
                  <div className="text-slate-400 text-left">Truly suspicious</div>
                  <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800 text-emerald-300 font-bold">{m.filing.confusion.true_positives}</div>
                  <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800 text-rose-300 font-bold">{m.filing.confusion.false_negatives}</div>
                  <div className="text-slate-400 text-left">Not suspicious</div>
                  <div className="p-3 rounded-lg bg-amber-950/40 border border-amber-800 text-amber-300 font-bold">{m.filing.confusion.false_positives}</div>
                  <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800 text-emerald-300 font-bold">{m.filing.confusion.true_negatives}</div>
                </div>
              </div>
              <div className="overflow-x-auto rounded-xl border border-slate-800">
                <table className="w-full text-xs">
                  <thead className="bg-slate-900 text-slate-400"><tr><th className="text-left p-2.5">Alert type</th><th className="text-right p-2.5">Cases</th><th className="text-right p-2.5">Filed</th><th className="text-right p-2.5">Truly susp.</th><th className="text-right p-2.5">Correct</th></tr></thead>
                  <tbody>
                    {Object.entries(m.filing.by_alert_type).map(([k, v]) => (
                      <tr key={k} className="border-t border-slate-800 text-slate-300">
                        <td className="p-2.5">{label(k)}</td><td className="p-2.5 text-right">{v.cases}</td><td className="p-2.5 text-right">{v.filed}</td>
                        <td className="p-2.5 text-right">{v.true_suspicious}</td><td className="p-2.5 text-right">{pct(v.correct / Math.max(1, v.cases))}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          {/* Stage 3 */}
          <section className="space-y-4">
            <StageHeader n={3} icon={<ShieldCheck className="h-5 w-5" />} title="Fact checking"
              question="Is every claim in a report backed by the ledger — and are corrupted reports caught?" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Stat title="Genuine reports verified" value={pct(m.fact_check.genuine_reports_ready)} tone="good" />
              <Stat title="Claims grounded" value={pct(m.fact_check.mean_grounding_rate)} tone="good" />
              <Stat title="5W1H completeness" value={pct(m.fact_check.mean_completeness_5w1h)} />
              <Stat title="Corrupted reports caught" value={pct(m.fact_check.corruption_catch_rate)} tone="good" hint={`${m.fact_check.corrupted_reports_tested} deliberately corrupted reports`} />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
              {Object.entries(m.fact_check.catch_rate_by_corruption).map(([k, v]) => (
                <div key={k} className="p-3 rounded-lg border border-slate-800 bg-surface text-xs">
                  <div className="text-slate-400">{label(k)}</div>
                  <div className="text-lg font-bold text-slate-100">{pct(v)}</div>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
};
