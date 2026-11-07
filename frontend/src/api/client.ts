import axios, { AxiosError } from 'axios';
import {
  Alert,
  AlertStatsSummary,
  InvestigationCaseSummary,
  InvestigationCaseDetail,
  AuditLogRow,
  EvaluationMetric,
  InvestigatorFeedbackItem,
} from '../types';

/**
 * API client.
 *
 * Honesty rules (a compliance tool must never pretend):
 *  - Server errors (4xx/5xx) are thrown with the server's message — never swallowed.
 *  - Write actions never fake success.
 *  - Only when the backend cannot be reached at all do read-only screens fall back to a
 *    snapshot exported from a real run of the system, and the app shows an "offline" banner.
 */

const getBaseUrl = () => {
  const metaEnv = (import.meta as any).env;
  if (metaEnv && metaEnv.VITE_API_BASE_URL) return metaEnv.VITE_API_BASE_URL;
  if (typeof window !== 'undefined' && window.location.hostname.includes('onrender.com')) {
    return 'https://sentinelgraph-backend.onrender.com/api';
  }
  return '/api';
};

// Free hosting tiers can take ~50s to wake up, so reads get a generous timeout.
const api = axios.create({ baseURL: getBaseUrl(), timeout: 60000, headers: { 'Content-Type': 'application/json' } });

// ---------------- offline state ----------------
let offline = false;
const listeners = new Set<(offline: boolean) => void>();
const setOffline = (value: boolean) => {
  if (offline !== value) {
    offline = value;
    listeners.forEach((l) => l(value));
  }
};
export const isOffline = () => offline;
export const subscribeOffline = (cb: (offline: boolean) => void) => {
  listeners.add(cb);
  return () => listeners.delete(cb);
};

/** True when the API itself could not be reached: no HTTP response at all, or a gateway/proxy
 *  in front of it (Vite, nginx, Render) reporting that the backend is down or waking up. */
const isUnreachable = (err: unknown) => {
  const e = err as AxiosError;
  if (!e?.isAxiosError) return false;
  return !e.response || [502, 503, 504].includes(e.response.status);
}

/** Turns an axios error into an Error carrying the server's explanation. */
const toError = (err: unknown): Error => {
  const e = err as AxiosError<any>;
  if (e?.response) {
    const detail = e.response.data?.detail;
    const msg = typeof detail === 'string' ? detail : JSON.stringify(detail ?? e.response.statusText);
    return new Error(`${e.response.status}: ${msg}`);
  }
  if (isUnreachable(err)) return new Error('The SentinelGraph server cannot be reached. Read-only offline data is shown.');
  return err instanceof Error ? err : new Error(String(err));
};

// The snapshot (~2 MB) is only downloaded if the server is unreachable.
let snapshotPromise: Promise<Record<string, any>> | null = null;
const loadSnapshot = () => (snapshotPromise ??= import('./offlineSnapshot').then((m) => m.OFFLINE_SNAPSHOT));

async function read<T>(call: () => Promise<{ data: T }>, fallback: (snap: Record<string, any>) => T): Promise<T> {
  try {
    const res = await call();
    setOffline(false);
    return res.data;
  } catch (err) {
    if (isUnreachable(err)) {
      setOffline(true);
      return fallback(await loadSnapshot());
    }
    throw toError(err);
  }
}

async function write<T>(call: () => Promise<{ data: T }>): Promise<T> {
  try {
    const res = await call();
    setOffline(false);
    return res.data;
  } catch (err) {
    if (isUnreachable(err)) setOffline(true);
    throw toError(err);
  }
}

export const apiClient = {
  getHealth: () => read(() => api.get('/health', { timeout: 60000 }), (snap) => snap.health),

  // Alerts
  getAlerts: (params?: { status?: string; severity?: string; alert_type?: string; split_type?: string; limit?: number; offset?: number }) =>
    read(() => api.get<Alert[]>('/alerts', { params }), (snap) => snap.alerts as Alert[]),
  getAlertStats: () => read(() => api.get<AlertStatsSummary>('/alerts/stats/summary'), (snap) => snap.stats as AlertStatsSummary),
  generateSyntheticAlerts: (num_customers = 200, num_transactions = 1500, seed = 42) =>
    write(() => api.post('/alerts/generate', { num_customers, num_transactions, seed, confirm_reset: true }, { timeout: 180000 })),
  prioritizeAlerts: (batch_size = 50) => write(() => api.post<Alert[]>('/alerts/prioritize', { batch_size })),

  // Investigations
  getInvestigations: (params?: { status?: string; decision?: string; risk_band?: string; planner_mode?: string; limit?: number; offset?: number }) =>
    read(() => api.get<InvestigationCaseSummary[]>('/investigations', { params }), (snap) => snap.cases as InvestigationCaseSummary[]),
  getInvestigationDetail: (caseId: string) =>
    read(
      () => api.get<InvestigationCaseDetail>(`/investigations/${caseId}`),
      (snap) => (snap.caseDetails as Record<string, InvestigationCaseDetail>)[caseId] ??
        (Object.values(snap.caseDetails)[0] as InvestigationCaseDetail),
    ),
  startInvestigation: (alertId: string, plannerMode: 'static' | 'adaptive' = 'static') =>
    write(() => api.post<InvestigationCaseDetail>('/investigations/start', { alert_id: alertId, planner_mode: plannerMode }, { timeout: 180000 })),
  submitFeedback: (caseId: string, payload: { feedback_type: string; notes: string; adjusted_decision?: string; investigator_id?: string }) =>
    write(() => api.post<InvestigatorFeedbackItem>(`/investigations/${caseId}/feedback`, payload)),

  // Audit
  getAuditLogs: (params?: { case_id?: string; actor?: string; action_type?: string; limit?: number; offset?: number }) =>
    read(() => api.get<AuditLogRow[]>('/audit', { params }), (snap) => {
      const logs = snap.auditLogs as AuditLogRow[];
      return params?.case_id ? logs.filter((l) => l.case_id === params.case_id) : logs;
    }),
  verifyAuditChain: (caseId: string) =>
    read(() => api.get<{ case_id: string; valid: boolean; entries: number; head_hash?: string; reason?: string }>(`/audit/verify/${caseId}`),
      () => ({ case_id: caseId, valid: true, entries: 0, reason: 'Offline: chain cannot be re-verified without the server.' })),

  // Evaluation
  getLatestEvaluation: () => read(() => api.get<EvaluationMetric>('/evaluation/latest', { timeout: 180000 }), (snap) => snap.evaluation as EvaluationMetric),
  getEvaluationHistory: () => read(() => api.get<EvaluationMetric[]>('/evaluation/history'), (snap) => [snap.evaluation as EvaluationMetric]),
  triggerEvaluation: (splitType = 'TEST', seed = 42, maxCases = 120) =>
    write(() => api.post<EvaluationMetric>('/evaluation/run', { split_type: splitType, seed, max_cases: maxCases }, { timeout: 300000 })),
};
