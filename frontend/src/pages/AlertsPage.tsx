import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bot, RefreshCw, AlertCircle } from 'lucide-react';
import { apiClient } from '../api/client';
import { Alert } from '../types';
import { RiskBadge } from '../components/RiskBadge';
import { ALERT_TYPE_LABEL, alertTypeLabel, getPlannerMode } from '../labels';

/** Raw alerts from monitoring. The analyst picks one and the agents investigate it. */
export const AlertsPage: React.FC = () => {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [investigatingId, setInvestigatingId] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [search, setSearch] = useState('');

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      setAlerts(await apiClient.getAlerts({
        severity: severityFilter || undefined,
        alert_type: typeFilter || undefined,
        limit: 100,
      }));
    } catch (err) {
      window.alert(`Could not fetch alerts. ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [severityFilter, typeFilter]);

  const investigate = async (alertId: string) => {
    setInvestigatingId(alertId);
    try {
      const res = await apiClient.startInvestigation(alertId, getPlannerMode());
      navigate(`/investigations/${res.case_id}`);
    } catch (err) {
      window.alert(`Could not start the investigation. ${err instanceof Error ? err.message : String(err)}`);
      setInvestigatingId(null);
    }
  };

  const q = search.toLowerCase();
  const shown = alerts.filter((a) =>
    !q || [a.alert_id, a.entity_id, a.trigger_reason, alertTypeLabel(a.alert_type)].some((v) => v.toLowerCase().includes(q)),
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Alerts</h1>
          <p className="text-sm text-slate-400 mt-1">
            Raised by monitoring rules and the anomaly model. Click <strong>Investigate</strong> and the agents build the case for you (about a second).
          </p>
        </div>
        <button onClick={fetchAlerts} className="self-start md:self-auto px-3 py-2 rounded-xl bg-surface border border-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1.5">
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </button>
      </div>

      <div className="p-3 rounded-2xl bg-surface border border-slate-800 flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[220px] relative">
          <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by account, alert or reason…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-background border border-slate-800 rounded-xl text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
          />
        </div>
        <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}
          className="px-3 py-2 bg-background border border-slate-800 rounded-xl text-xs text-slate-300">
          <option value="">All severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 bg-background border border-slate-800 rounded-xl text-xs text-slate-300">
          <option value="">All patterns</option>
          {Object.entries(ALERT_TYPE_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>

      <div className="bg-surface border border-slate-800 rounded-2xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading alerts…</div>
        ) : shown.length === 0 ? (
          <div className="p-12 text-center text-slate-500 space-y-2">
            <AlertCircle className="h-8 w-8 mx-auto text-slate-600" />
            <p className="text-sm">No alerts match these filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 text-xs">
                  <th className="py-3 px-4">Pattern</th>
                  <th className="py-3 px-4">What happened</th>
                  <th className="py-3 px-4">Account</th>
                  <th className="py-3 px-4">Severity</th>
                  <th className="py-3 px-4 text-right" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {shown.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-800/40">
                    <td className="py-3 px-4 whitespace-nowrap font-semibold text-slate-200">{alertTypeLabel(a.alert_type)}</td>
                    <td className="py-3 px-4 max-w-md text-slate-300 text-xs" title={a.trigger_reason}>
                      <span className="line-clamp-2">{a.trigger_reason}</span>
                    </td>
                    <td className="py-3 px-4 font-mono text-xs text-slate-400">{a.entity_id}</td>
                    <td className="py-3 px-4"><RiskBadge band={a.severity} score={a.raw_score} size="sm" /></td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => investigate(a.alert_id)}
                        disabled={investigatingId === a.alert_id}
                        className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold inline-flex items-center gap-1.5"
                      >
                        <Bot className="h-3.5 w-3.5" />
                        {investigatingId === a.alert_id ? 'Investigating…' : 'Investigate'}
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
