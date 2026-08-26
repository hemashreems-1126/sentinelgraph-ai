import axios from 'axios';
import {
  Alert,
  AlertStatsSummary,
  InvestigationCaseSummary,
  InvestigationCaseDetail,
  AuditLogRow,
  EvaluationMetric,
  InvestigatorFeedbackItem
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiClient = {
  // Health
  getHealth: async () => {
    const res = await api.get('/health');
    return res.data;
  },

  // Alerts
  getAlerts: async (params?: { status?: string; severity?: string; alert_type?: string; split_type?: string; limit?: number; offset?: number }) => {
    const res = await api.get<Alert[]>('/alerts', { params });
    return res.data;
  },

  getAlertStats: async () => {
    const res = await api.get<AlertStatsSummary>('/alerts/stats/summary');
    return res.data;
  },

  generateSyntheticAlerts: async (num_customers = 200, num_transactions = 1500, seed = 42) => {
    const res = await api.post('/alerts/generate', { num_customers, num_transactions, seed });
    return res.data;
  },

  prioritizeAlerts: async (batch_size = 50) => {
    const res = await api.post<Alert[]>('/alerts/prioritize', { batch_size });
    return res.data;
  },

  // Investigations
  getInvestigations: async (params?: { status?: string; decision?: string; risk_band?: string; planner_mode?: string; limit?: number; offset?: number }) => {
    const res = await api.get<InvestigationCaseSummary[]>('/investigations', { params });
    return res.data;
  },

  getInvestigationDetail: async (caseId: string) => {
    const res = await api.get<InvestigationCaseDetail>(`/investigations/${caseId}`);
    return res.data;
  },

  startInvestigation: async (alertId: string, plannerMode: 'static' | 'adaptive' = 'static') => {
    const res = await api.post<InvestigationCaseDetail>('/investigations/start', {
      alert_id: alertId,
      planner_mode: plannerMode
    });
    return res.data;
  },

  submitFeedback: async (caseId: string, payload: { feedback_type: string; notes: string; adjusted_decision?: string; investigator_id?: string }) => {
    const res = await api.post<InvestigatorFeedbackItem>(`/investigations/${caseId}/feedback`, payload);
    return res.data;
  },

  // Audit Logs
  getAuditLogs: async (params?: { case_id?: string; actor?: string; action_type?: string; limit?: number; offset?: number }) => {
    const res = await api.get<AuditLogRow[]>('/audit', { params });
    return res.data;
  },

  // Evaluation
  getLatestEvaluation: async () => {
    const res = await api.get<EvaluationMetric>('/evaluation/latest');
    return res.data;
  },

  getEvaluationHistory: async () => {
    const res = await api.get<EvaluationMetric[]>('/evaluation/history');
    return res.data;
  },

  triggerEvaluation: async (splitType = 'TEST', seed = 42) => {
    const res = await api.post<EvaluationMetric>('/evaluation/run', { split_type: splitType, seed });
    return res.data;
  },
};
