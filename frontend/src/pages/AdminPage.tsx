import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Database, ArrowUpDown, Route, BarChart3 } from 'lucide-react';
import { apiClient } from '../api/client';
import { getPlannerMode, setPlannerMode } from '../labels';

/** Controls for running the demo. Kept off the analyst screens on purpose. */
export const AdminPage: React.FC = () => {
  const navigate = useNavigate();
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [planner, setPlanner] = useState(getPlannerMode());

  const run = async (key: string, action: () => Promise<unknown>, done: string) => {
    setBusy(key);
    setMessage(null);
    try {
      await action();
      setMessage(done);
    } catch (err) {
      setMessage(`Failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setBusy(null);
    }
  };

  const card = (icon: React.ReactNode, title: string, body: React.ReactNode, action: React.ReactNode) => (
    <div className="p-5 rounded-2xl bg-surface border border-slate-800 flex flex-col md:flex-row md:items-center gap-4">
      <div className="p-2.5 rounded-xl bg-indigo-950/70 text-indigo-300 border border-indigo-500/30 self-start">{icon}</div>
      <div className="flex-1 space-y-1">
        <h3 className="text-sm font-bold text-slate-100">{title}</h3>
        <div className="text-xs text-slate-400">{body}</div>
      </div>
      <div className="shrink-0">{action}</div>
    </div>
  );
  const btn = 'px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-bold';

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-extrabold text-white tracking-tight">Demo controls</h1>
        <p className="text-sm text-slate-400 mt-1">For running and showing the project. Analysts don't need anything on this page.</p>
      </div>

      {message && <div className="p-3 rounded-xl border border-slate-700 bg-slate-900 text-sm text-slate-200">{message}</div>}

      {card(<Database className="h-5 w-5" />, 'Generate a new synthetic dataset',
        <>Creates a fresh INR ledger with laundering patterns and legitimate look-alikes, then runs monitoring.
          <strong className="text-amber-300"> This replaces all current alerts, cases and audit logs.</strong></>,
        <button className={btn} disabled={busy !== null}
          onClick={() => window.confirm('Replace ALL current alerts, cases and audit logs with a new synthetic dataset?') &&
            run('gen', () => apiClient.generateSyntheticAlerts(200, 1500, 42), 'New dataset generated. Open Alerts to see it.')}>
          {busy === 'gen' ? 'Generating…' : 'Generate'}
        </button>)}

      {card(<ArrowUpDown className="h-5 w-5" />, 'Re-rank the alert queue',
        'Re-orders pending alerts by severity and customer risk.',
        <button className={btn} disabled={busy !== null} onClick={() => run('rank', () => apiClient.prioritizeAlerts(100), 'Alert queue re-ranked.')}>
          {busy === 'rank' ? 'Ranking…' : 'Re-rank'}
        </button>)}

      {card(<Route className="h-5 w-5" />, 'Investigation plan',
        <>Standard checklist (default, no LLM needed) or an adaptive plan written by the LLM when a Groq key is configured. Saved in this browser.</>,
        <select value={planner} onChange={(e) => { const m = e.target.value as 'static' | 'adaptive'; setPlanner(m); setPlannerMode(m); }}
          className="px-3 py-2 bg-background border border-slate-700 rounded-xl text-xs text-slate-200">
          <option value="static">Standard checklist</option>
          <option value="adaptive">Adaptive (LLM)</option>
        </select>)}

      {card(<BarChart3 className="h-5 w-5" />, 'Evaluation',
        'Measure detection, filing decisions and fact checking on held-out alerts.',
        <button className={btn} onClick={() => navigate('/evaluation')}>Open evaluation</button>)}
    </div>
  );
};
