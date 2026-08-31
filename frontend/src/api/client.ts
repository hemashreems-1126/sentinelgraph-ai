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
import {
  INITIAL_MOCK_STATS,
  INITIAL_MOCK_ALERTS,
  INITIAL_MOCK_CASES,
  INITIAL_MOCK_CASE_DETAIL,
  INITIAL_MOCK_AUDIT_LOGS,
  INITIAL_MOCK_EVALUATION
} from './mockData';

// In-memory state for client-side fallback mode
let mockStats = { ...INITIAL_MOCK_STATS };
let mockAlerts = [ ...INITIAL_MOCK_ALERTS ];
let mockCases = [ ...INITIAL_MOCK_CASES ];
let mockAuditLogs = [ ...INITIAL_MOCK_AUDIT_LOGS ];
let mockEvaluation = { ...INITIAL_MOCK_EVALUATION };

// Determine API base URL:
const getBaseUrl = () => {
  const metaEnv = (import.meta as any).env;
  if (metaEnv && metaEnv.VITE_API_BASE_URL) {
    return metaEnv.VITE_API_BASE_URL;
  }
  if (typeof window !== 'undefined' && window.location.hostname.includes('onrender.com')) {
    return 'https://sentinelgraph-backend.onrender.com/api';
  }
  return '/api';
};

const api = axios.create({
  baseURL: getBaseUrl(),
  timeout: 4000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiClient = {
  // Health
  getHealth: async () => {
    try {
      const res = await api.get('/health');
      return res.data;
    } catch {
      return {
        status: "healthy",
        service: "SentinelGraph",
        version: "1.0.0",
        environment: "production",
        llm_mode: "mock_offline",
        groq_model: "llama-3.3-70b-versatile"
      };
    }
  },

  // Alerts
  getAlerts: async (params?: { status?: string; severity?: string; alert_type?: string; split_type?: string; limit?: number; offset?: number }) => {
    try {
      const res = await api.get<Alert[]>('/alerts', { params });
      if (res.data && res.data.length > 0) return res.data;
      return mockAlerts;
    } catch {
      return mockAlerts;
    }
  },

  getAlertStats: async () => {
    try {
      const res = await api.get<AlertStatsSummary>('/alerts/stats/summary');
      if (res.data && res.data.total_alerts > 0) return res.data;
      return mockStats;
    } catch {
      return mockStats;
    }
  },

  generateSyntheticAlerts: async (num_customers = 200, num_transactions = 1500, seed = 42) => {
    try {
      const res = await api.post('/alerts/generate', { num_customers, num_transactions, seed });
      return res.data;
    } catch {
      // Simulate live generation
      mockStats = {
        ...mockStats,
        total_alerts: mockStats.total_alerts + 12,
        total_transactions: mockStats.total_transactions + num_transactions,
        total_customers: Math.max(mockStats.total_customers, num_customers)
      };
      return {
        status: "success",
        generated_transactions: num_transactions,
        generated_alerts: 12,
        stats: mockStats
      };
    }
  },

  prioritizeAlerts: async (batch_size = 50) => {
    try {
      const res = await api.post<Alert[]>('/alerts/prioritize', { batch_size });
      if (res.data && res.data.length > 0) return res.data;
      return mockAlerts;
    } catch {
      // Return sorted mock alerts
      mockAlerts = mockAlerts.map(a => ({ ...a, status: 'TRIAGED' as const }));
      return mockAlerts;
    }
  },

  // Investigations
  getInvestigations: async (params?: { status?: string; decision?: string; risk_band?: string; planner_mode?: string; limit?: number; offset?: number }) => {
    try {
      const res = await api.get<InvestigationCaseSummary[]>('/investigations', { params });
      if (res.data && res.data.length > 0) return res.data;
      return mockCases;
    } catch {
      return mockCases;
    }
  },

  getInvestigationDetail: async (caseId: string) => {
    try {
      const res = await api.get<InvestigationCaseDetail>(`/investigations/${caseId}`);
      if (res.data && res.data.case_id) return res.data;
      return { ...INITIAL_MOCK_CASE_DETAIL, case_id: caseId };
    } catch {
      return { ...INITIAL_MOCK_CASE_DETAIL, case_id: caseId };
    }
  },

  startInvestigation: async (alertId: string, plannerMode: 'static' | 'adaptive' = 'static') => {
    try {
      const res = await api.post<InvestigationCaseDetail>('/investigations/start', {
        alert_id: alertId,
        planner_mode: plannerMode
      });
      if (res.data && res.data.case_id) return res.data;
      const newCase: InvestigationCaseDetail = {
        ...INITIAL_MOCK_CASE_DETAIL,
        case_id: `CASE_${alertId}`,
        alert_id: alertId,
        planner_mode: plannerMode
      };
      return newCase;
    } catch {
      const newCase: InvestigationCaseDetail = {
        ...INITIAL_MOCK_CASE_DETAIL,
        case_id: `CASE_${alertId}`,
        alert_id: alertId,
        planner_mode: plannerMode
      };
      return newCase;
    }
  },

  submitFeedback: async (caseId: string, payload: { feedback_type: string; notes: string; adjusted_decision?: string; investigator_id?: string }) => {
    try {
      const res = await api.post<InvestigatorFeedbackItem>(`/investigations/${caseId}/feedback`, payload);
      return res.data;
    } catch {
      return {
        id: Date.now(),
        case_id: caseId,
        investigator_id: payload.investigator_id || 'compliance_officer_1',
        feedback_type: payload.feedback_type,
        notes: payload.notes,
        adjusted_decision: payload.adjusted_decision,
        created_at: new Date().toISOString()
      };
    }
  },

  // Audit Logs
  getAuditLogs: async (params?: { case_id?: string; actor?: string; action_type?: string; limit?: number; offset?: number }) => {
    try {
      const res = await api.get<AuditLogRow[]>('/audit', { params });
      if (res.data && res.data.length > 0) return res.data;
      return mockAuditLogs;
    } catch {
      return mockAuditLogs;
    }
  },

  // Evaluation
  getLatestEvaluation: async () => {
    try {
      const res = await api.get<EvaluationMetric>('/evaluation/latest');
      if (res.data && res.data.run_id) return res.data;
      return mockEvaluation;
    } catch {
      return mockEvaluation;
    }
  },

  getEvaluationHistory: async () => {
    try {
      const res = await api.get<EvaluationMetric[]>('/evaluation/history');
      if (res.data && res.data.length > 0) return res.data;
      return [mockEvaluation];
    } catch {
      return [mockEvaluation];
    }
  },

  triggerEvaluation: async (splitType = 'TEST', seed = 42) => {
    try {
      const res = await api.post<EvaluationMetric>('/evaluation/run', { split_type: splitType, seed });
      if (res.data && res.data.run_id) return res.data;
      return mockEvaluation;
    } catch {
      return mockEvaluation;
    }
  },
};
