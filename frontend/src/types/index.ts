export type RiskBand = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type DecisionPolicy = 'ALLOW' | 'REVIEW' | 'BLOCK';
export type AlertSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type AlertStatus = 'PENDING' | 'TRIAGED' | 'INVESTIGATING' | 'CLOSED' | 'ESCALATED';

export interface Alert {
  id: number;
  alert_id: string;
  entity_type: string;
  entity_id: string;
  alert_type: string;
  severity: AlertSeverity;
  raw_score: number;
  priority_rank: number;
  status: AlertStatus;
  trigger_reason: string;
  features_json?: Record<string, any>;
  split_type: 'TRAIN' | 'TEST';
  created_at: string;
  triaged_at?: string;
}

export interface AgentStep {
  agent_name: string;
  action: string;
  status: string;
  duration_ms: number;
  summary: string;
  details: Record<string, any>;
  timestamp: string;
}

export interface HypothesisItem {
  id: number;
  hypothesis_id: string;
  title: string;
  description: string;
  probability: number;
  status: 'SUPPORTED' | 'REFUTED' | 'INCONCLUSIVE';
  corroborating_evidence?: string[];
  contradicting_evidence?: string[];
}

export interface AuditLogRow {
  id: number;
  case_id?: string;
  alert_id?: string;
  actor: string;
  action_type: string;
  description: string;
  input_payload?: Record<string, any>;
  output_payload?: Record<string, any>;
  execution_time_ms: number;
  verification_hash: string;
  prev_hash?: string;
  timestamp: string;
}

export interface InvestigatorFeedbackItem {
  id: number;
  case_id: string;
  investigator_id: string;
  feedback_type: string;
  notes: string;
  adjusted_decision?: string;
  created_at: string;
}

export interface InvestigationCaseDetail {
  id: number;
  case_id: string;
  alert_id: string;
  planner_mode: 'static' | 'adaptive';
  status: string;
  iterations_count: number;
  final_risk_score: number;
  final_risk_band: RiskBand;
  final_decision: DecisionPolicy;
  decision_rationale?: string;
  created_at: string;
  completed_at?: string;
  plan_json?: Record<string, any>;
  hypotheses_json?: any[];
  subagent_evidence_json?: Record<string, any>;
  reasoning_json?: Record<string, any>;
  sar_report_text?: string;
  sar_narrative_json?: Record<string, any>;
  agent_trail_json?: AgentStep[];
  hypotheses: HypothesisItem[];
  audit_logs: AuditLogRow[];
  feedback: InvestigatorFeedbackItem[];
}

export interface InvestigationCaseSummary {
  id: number;
  case_id: string;
  alert_id: string;
  planner_mode: string;
  status: string;
  iterations_count: number;
  final_risk_score: number;
  final_risk_band: RiskBand;
  final_decision: DecisionPolicy;
  filing_decision?: 'FILE_STR' | 'NO_FILE' | null;
  filing_tier?: string | null;
  report_status?: string | null;
  decision_rationale?: string;
  created_at: string;
  completed_at?: string;
}

export interface EvaluationMetric {
  run_id: string;
  timestamp: string;
  split_type: string;
  total_samples: number;
  true_positives: number;
  false_positives: number;
  true_negatives: number;
  false_negatives: number;
  precision_score: number;
  recall_score: number;
  f1_score: number;
  accuracy_score: number;
  roc_auc: number;
  confusion_matrix_json: {
    true_positives: number;
    false_positives: number;
    true_negatives: number;
    false_negatives: number;
  };
  classification_report_json: Record<string, any>;
  metrics_json?: EvaluationStages;
  dataset_name?: string;
}

export interface EvaluationStages {
  dataset: string;
  split: string;
  runtime_seconds: number;
  ground_truth: string;
  detection: {
    alerts_evaluated: number;
    alert_precision: number;
    controlled_accounts: number;
    controlled_account_coverage: number;
    by_alert_type: Record<string, { alerts: number; true_suspicious: number; precision: number }>;
  };
  filing: {
    cases_investigated: number;
    confusion: { true_positives: number; false_positives: number; false_negatives: number; true_negatives: number };
    precision: number;
    recall: number;
    f1: number;
    accuracy: number;
    risk_score_roc_auc: number;
    alert_reduction_rate: number;
    hard_negative_cases: number;
    hard_negative_false_file_rate: number;
    tier_distribution: Record<string, number>;
    avg_seconds_per_case: number;
    by_alert_type: Record<string, { cases: number; filed: number; true_suspicious: number; correct: number }>;
  };
  fact_check: {
    genuine_reports: number;
    mean_grounding_rate: number;
    genuine_reports_ready: number;
    mean_completeness_5w1h: number;
    corrupted_reports_tested: number;
    corruption_catch_rate: number;
    catch_rate_by_corruption: Record<string, number>;
  };
}

export interface AlertStatsSummary {
  total_alerts: number;
  pending_alerts: number;
  triaged_alerts: number;
  investigating_alerts: number;
  closed_alerts: number;
  escalated_alerts: number;
  total_customers: number;
  total_transactions: number;
  fraud_transactions: number;
  total_cases_investigated: number;
  alert_type_breakdown: Record<string, number>;
  severity_breakdown: Record<string, number>;
}
