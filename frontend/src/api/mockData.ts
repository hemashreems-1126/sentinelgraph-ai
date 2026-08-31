import {
  Alert,
  AlertStatsSummary,
  InvestigationCaseSummary,
  InvestigationCaseDetail,
  AuditLogRow,
  EvaluationMetric,
  InvestigatorFeedbackItem
} from '../types';

export const INITIAL_MOCK_STATS: AlertStatsSummary = {
  total_alerts: 64,
  pending_alerts: 42,
  triaged_alerts: 16,
  investigating_alerts: 2,
  closed_alerts: 4,
  escalated_alerts: 0,
  total_customers: 200,
  total_transactions: 1435,
  fraud_transactions: 172,
  total_cases_investigated: 6,
  alert_type_breakdown: {
    STRUCTURING: 22,
    LAYERING: 18,
    MULE_ACCOUNT: 14,
    VELOCITY_ABUSE: 6,
    ISOLATION_FOREST: 4
  },
  severity_breakdown: {
    CRITICAL: 16,
    HIGH: 24,
    MEDIUM: 18,
    LOW: 6
  }
};

export const INITIAL_MOCK_ALERTS: Alert[] = [
  {
    id: 1,
    alert_id: "ALT_STRUCT_8821",
    entity_type: "ACCOUNT",
    entity_id: "ACC_CUST_0042_1",
    alert_type: "STRUCTURING",
    severity: "CRITICAL",
    raw_score: 94.5,
    priority_rank: 1,
    status: "TRIAGED",
    trigger_reason: "5 consecutive cash/wire deposits between $9,200 and $9,950 within 4 hours (CTR Avoidance)",
    features_json: { velocity_1h: 5, total_amount: 48350, z_score: 4.82, counterparty_count: 5 },
    split_type: "TEST",
    created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
    triaged_at: new Date(Date.now() - 3600000 * 1).toISOString()
  },
  {
    id: 2,
    alert_id: "ALT_LAYER_4492",
    entity_type: "TRANSACTION",
    entity_id: "TXN_FRAUD_00018",
    alert_type: "LAYERING",
    severity: "CRITICAL",
    raw_score: 91.0,
    priority_rank: 2,
    status: "TRIAGED",
    trigger_reason: "Rapid 4-hop circular wire pass-through across shell accounts within 35 minutes",
    features_json: { hop_count: 4, total_chain_amount: 88200, dissipation_rate: 0.04 },
    split_type: "TEST",
    created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
    triaged_at: new Date(Date.now() - 3600000 * 2).toISOString()
  },
  {
    id: 3,
    alert_id: "ALT_MULE_1109",
    entity_type: "ACCOUNT",
    entity_id: "ACC_CUST_0089_1",
    alert_type: "MULE_ACCOUNT",
    severity: "CRITICAL",
    raw_score: 88.5,
    priority_rank: 3,
    status: "TRIAGED",
    trigger_reason: "Dormant personal account received sudden $62,000 wire and drained 96% in 18 minutes",
    features_json: { dormancy_days: 140, spike_amount: 62000, drain_ratio: 0.96 },
    split_type: "TEST",
    created_at: new Date(Date.now() - 3600000 * 6).toISOString(),
    triaged_at: new Date(Date.now() - 3600000 * 3).toISOString()
  },
  {
    id: 4,
    alert_id: "ALT_VELOC_7731",
    entity_type: "ACCOUNT",
    entity_id: "ACC_CUST_0114_2",
    alert_type: "VELOCITY_ABUSE",
    severity: "HIGH",
    raw_score: 79.0,
    priority_rank: 4,
    status: "PENDING",
    trigger_reason: "8 rapid API card payments totaling $24,800 sent to high-risk merchant in 12 minutes",
    features_json: { txns_in_15m: 8, avg_interval_sec: 90, total_amount: 24800 },
    split_type: "TRAIN",
    created_at: new Date(Date.now() - 3600000 * 8).toISOString()
  },
  {
    id: 5,
    alert_id: "ALT_IFOREST_3021",
    entity_type: "TRANSACTION",
    entity_id: "TXN_FRAUD_00064",
    alert_type: "ISOLATION_FOREST",
    severity: "HIGH",
    raw_score: 76.5,
    priority_rank: 5,
    status: "PENDING",
    trigger_reason: "Multidimensional anomaly detected by Isolation Forest (Anomaly Score: -0.742)",
    features_json: { anomaly_score: -0.742, amount_percentile: 99.4, time_of_day_deviation: 3.2 },
    split_type: "TEST",
    created_at: new Date(Date.now() - 3600000 * 10).toISOString()
  },
  {
    id: 6,
    alert_id: "ALT_STRUCT_5512",
    entity_type: "ACCOUNT",
    entity_id: "ACC_CUST_0019_1",
    alert_type: "STRUCTURING",
    severity: "HIGH",
    raw_score: 74.0,
    priority_rank: 6,
    status: "PENDING",
    trigger_reason: "3 cash branch deposits of $9,800 across 2 separate locations in 48 hours",
    features_json: { deposit_count: 3, branch_locations: 2, total_amount: 29400 },
    split_type: "TRAIN",
    created_at: new Date(Date.now() - 3600000 * 12).toISOString()
  }
];

export const INITIAL_MOCK_CASES: InvestigationCaseSummary[] = [
  {
    id: 1,
    case_id: "CASE_ALT_STRUCT_8821",
    alert_id: "ALT_STRUCT_8821",
    planner_mode: "adaptive",
    status: "COMPLETED",
    iterations_count: 1,
    final_risk_score: 92.5,
    final_risk_band: "CRITICAL",
    final_decision: "BLOCK",
    decision_rationale: "Deterministic composite risk score is 92.5/100 (CRITICAL). 5 sub-$10,000 deposits totaling $48,350 detected with high velocity Z-score (+4.82) and 2-hop linkage to an offshore shell entity.",
    created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
    completed_at: new Date(Date.now() - 3600000 * 1.9).toISOString()
  },
  {
    id: 2,
    case_id: "CASE_ALT_LAYER_4492",
    alert_id: "ALT_LAYER_4492",
    planner_mode: "static",
    status: "COMPLETED",
    iterations_count: 1,
    final_risk_score: 89.0,
    final_risk_band: "CRITICAL",
    final_decision: "BLOCK",
    decision_rationale: "Deterministic composite risk score is 89.0/100 (CRITICAL). Multi-hop fund pass-through confirmed across 4 accounts with 96% retention within 35 minutes.",
    created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
    completed_at: new Date(Date.now() - 3600000 * 3.9).toISOString()
  },
  {
    id: 3,
    case_id: "CASE_ALT_MULE_1109",
    alert_id: "ALT_MULE_1109",
    planner_mode: "adaptive",
    status: "COMPLETED",
    iterations_count: 2,
    final_risk_score: 86.0,
    final_risk_band: "CRITICAL",
    final_decision: "BLOCK",
    decision_rationale: "Deterministic composite risk score is 86.0/100 (CRITICAL). Classic money mule profile: 140 days dormancy followed by $62,000 incoming wire and immediate 96% outbound transfer.",
    created_at: new Date(Date.now() - 3600000 * 6).toISOString(),
    completed_at: new Date(Date.now() - 3600000 * 5.8).toISOString()
  }
];

export const INITIAL_MOCK_CASE_DETAIL: InvestigationCaseDetail = {
  id: 1,
  case_id: "CASE_ALT_STRUCT_8821",
  alert_id: "ALT_STRUCT_8821",
  planner_mode: "adaptive",
  status: "COMPLETED",
  iterations_count: 1,
  final_risk_score: 92.5,
  final_risk_band: "CRITICAL",
  final_decision: "BLOCK",
  decision_rationale: "Deterministic composite risk score is 92.5/100 (CRITICAL). High-velocity smurfing verified with 2-hop linkage to high-risk offshore entity. Immediate account freeze and FinCEN SAR filing mandated.",
  created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
  completed_at: new Date(Date.now() - 3600000 * 1.9).toISOString(),
  plan_json: {
    mode: "adaptive",
    steps: [
      { step: 1, name: "Transaction History Extraction", agent: "EvidenceRetrievalAgent" },
      { step: 2, name: "2-Hop Counterparty Graph Traversal", agent: "GraphRelationshipAgent" },
      { step: 3, name: "Velocity & Z-Score Analysis", agent: "BehaviorAnalysisAgent" },
      { step: 4, name: "KYC & Occupation Document Review", agent: "DocumentAnalysisAgent" },
      { step: 5, name: "PEP & OFAC Sanctions Screening", agent: "ExternalIntelligenceAgent" },
      { step: 6, name: "Forensic Synthesis & Hypothesis Testing", agent: "AnalysisReasoningAgent" },
      { step: 7, name: "100% Deterministic Risk Scoring", agent: "RiskAssignmentAgent" },
      { step: 8, name: "FinCEN SAR Narrative Drafting", agent: "RegulatoryReportingAgent" },
      { step: 9, name: "Cryptographic SHA-256 Audit Logging", agent: "AuditingAgent" }
    ]
  },
  hypotheses_json: [
    {
      id: 1,
      hypothesis_id: "HYP_1",
      title: "Deliberate Structuring / Smurfing Scheme",
      description: "Customer intentionally splits a large $50,000 cash pool into sub-$10,000 deposits to evade Bank Secrecy Act CTR filing thresholds.",
      probability: 0.92,
      status: "SUPPORTED",
      corroborating_evidence: ["5 deposits between $9,200 and $9,950 within 4 hours", "Velocity Z-Score +4.82 sigma", "Shortest path to offshore intermediary: 2 hops"]
    },
    {
      id: 2,
      hypothesis_id: "HYP_2",
      title: "Legitimate Commercial Weekend Settlement",
      description: "High-volume commercial client processing organic retail customer payments over peak operational window.",
      probability: 0.08,
      status: "REFUTED",
      contradicting_evidence: ["KYC declared occupation is 'Digital Consultant', not retail merchant", "Counterparty accounts opened <30 days ago"]
    }
  ],
  subagent_evidence_json: {
    graph_evidence: {
      target_account: "ACC_CUST_0042_1",
      hop_1_counterparties: ["ACC_CUST_0012_1", "ACC_CUST_0033_2", "ACC_CUST_0078_1", "ACC_CUST_0091_1"],
      hop_2_counterparties: ["ACC_CUST_0155_1 (Sanctions High-Risk Flag)"],
      shortest_path_to_watchlist: 2,
      total_inflow_24h: 48350.00,
      total_outflow_24h: 46500.00
    },
    behavior_evidence: {
      z_score: 4.82,
      velocity_anomaly_ratio: 8.4,
      historical_daily_avg: 1250.00,
      current_24h_volume: 48350.00,
      baseline_variance_flag: "EXTREME_ANOMALY"
    },
    document_evidence: {
      declared_occupation: "Digital Marketing Agency",
      expected_monthly_turnover: "$15,000 - $30,000",
      actual_monthly_turnover: "$142,500",
      kyc_risk_tier: "MEDIUM",
      source_of_wealth_declared: "Client invoicing"
    },
    intelligence_evidence: {
      pep_match: false,
      ofac_sanctions_match: false,
      adverse_media_hits: 1,
      associated_high_risk_jurisdiction: "AE / BVI"
    }
  },
  reasoning_json: {
    synthesis: "Comprehensive analysis of transaction telemetry, 2-hop network graph topology, and KYC records firmly supports Hypothesis HYP_1 (Deliberate Structuring). The account exhibits an extreme +4.82 sigma velocity surge with 5 deposits just below the $10,000 CTR reporting limit, closely followed by an outbound wire to an unverified intermediary entity.",
    loop_back_required: false,
    confidence: 0.96
  },
  sar_report_text: `SUSPICIOUS ACTIVITY REPORT (SAR) NARRATIVE
======================================================================
FILING INSTITUTION: SentinelGraph AML Surveillance Platform
TARGET ENTITY: Customer CUST_0042 (Account: ACC_CUST_0042_1)
SUSPICIOUS ACTIVITY TYPE: Structuring / Smurfing & Fund Layering
SUSPICIOUS PERIOD: 2026-08-25 to 2026-08-27
TOTAL SUSPICIOUS AMOUNT: $48,350.00 USD

EXECUTIVE SUMMARY:
Between August 25 and August 27, 2026, Account ACC_CUST_0042_1 exhibited patterns characteristic of deliberate structuring under 31 U.S.C. 5324(a)(3). The account received five (5) distinct electronic and branch cash transfers ranging between $9,200.00 and $9,950.00 within a 4-hour window, totaling $48,350.00.

FORENSIC NETWORK FINDINGS:
Multi-hop graph traversal revealed that within 180 minutes of receipt, 96.1% of the aggregated capital was wired to Account ACC_CUST_0155_1, an entity flagged in commercial risk intelligence for connection to shell entity networks in offshore jurisdictions.

RECOMMENDATION:
1. Immediate restriction on outbound transfer capabilities on Account ACC_CUST_0042_1.
2. Formal transmission of this Suspicious Activity Report to FinCEN / competent FIU.
3. Enhanced Due Diligence (EDD) summons served to the primary beneficial owner.

COMPLIANCE OFFICER REVIEW:
STATUS: Pending Compliance Officer Sign-off / Human Investigator Override`,
  agent_trail_json: [
    {
      agent_name: "Supervisor",
      action: "INVESTIGATION_INITIALIZED",
      status: "COMPLETED",
      duration_ms: 45,
      summary: "Initialized LangGraph multi-agent forensic workflow for Alert ALT_STRUCT_8821",
      details: { alert_type: "STRUCTURING", severity: "CRITICAL" },
      timestamp: new Date(Date.now() - 3600000 * 2).toISOString()
    },
    {
      agent_name: "PlannerAgent",
      action: "DYNAMIC_PLAN_COMPOSED",
      status: "COMPLETED",
      duration_ms: 120,
      summary: "Generated 9-step investigative checklist with prioritized graph and behavior subagent execution",
      details: { planner_mode: "adaptive", steps_count: 9 },
      timestamp: new Date(Date.now() - 3600000 * 2 + 1000).toISOString()
    },
    {
      agent_name: "HypothesisAgent",
      action: "COMPETING_THEORIES_FORMULATED",
      status: "COMPLETED",
      duration_ms: 85,
      summary: "Formulated 2 competing hypotheses (Structuring Scheme vs Commercial Settlement)",
      details: { primary_hypothesis: "HYP_1", baseline_p: 0.70 },
      timestamp: new Date(Date.now() - 3600000 * 2 + 2000).toISOString()
    },
    {
      agent_name: "EvidenceRetrievalAgent",
      action: "LEDGER_DATA_INGESTED",
      status: "COMPLETED",
      duration_ms: 110,
      summary: "Extracted 45 past transactions and account balance history",
      details: { records_ingested: 45 },
      timestamp: new Date(Date.now() - 3600000 * 2 + 3000).toISOString()
    },
    {
      agent_name: "GraphRelationshipAgent",
      action: "2_HOP_NETWORK_TRAVERSED",
      status: "COMPLETED",
      duration_ms: 215,
      summary: "Built NetworkX graph: mapped 4 direct counterparties and 2-hop link to high-risk entity",
      details: { direct_nodes: 5, shortest_path_hops: 2 },
      timestamp: new Date(Date.now() - 3600000 * 2 + 4000).toISOString()
    },
    {
      agent_name: "BehaviorAnalysisAgent",
      action: "VELOCITY_ZSCORE_COMPUTED",
      status: "COMPLETED",
      duration_ms: 95,
      summary: "Detected +4.82 sigma velocity spike against 90-day baseline",
      details: { z_score: 4.82, risk_contribution: 20 },
      timestamp: new Date(Date.now() - 3600000 * 2 + 5000).toISOString()
    },
    {
      agent_name: "DocumentAnalysisAgent",
      action: "KYC_OCCUPATION_REVIEWED",
      status: "COMPLETED",
      duration_ms: 70,
      summary: "Identified 475% turnover mismatch against declared source of wealth",
      details: { turnover_mismatch_pct: 475 },
      timestamp: new Date(Date.now() - 3600000 * 2 + 6000).toISOString()
    },
    {
      agent_name: "ExternalIntelligenceAgent",
      action: "SANCTIONS_WATCHLIST_SCREENED",
      status: "COMPLETED",
      duration_ms: 65,
      summary: "Screened OFAC, PEP, and international sanctions registries",
      details: { ofac_hit: false, adverse_media_count: 1 },
      timestamp: new Date(Date.now() - 3600000 * 2 + 7000).toISOString()
    },
    {
      agent_name: "RiskAssignmentAgent",
      action: "DETERMINISTIC_SCORE_CALCULATED",
      status: "COMPLETED",
      duration_ms: 25,
      summary: "Computed 100% deterministic score: 92.5/100 -> CRITICAL band -> BLOCK policy",
      details: { score: 92.5, band: "CRITICAL", decision: "BLOCK" },
      timestamp: new Date(Date.now() - 3600000 * 2 + 8000).toISOString()
    },
    {
      agent_name: "RegulatoryReportingAgent",
      action: "FINCEN_SAR_DRAFTED",
      status: "COMPLETED",
      duration_ms: 140,
      summary: "Generated formal FinCEN SAR regulatory narrative draft",
      details: { suspicious_amount: 48350.00, filing_type: "SAR_STRUCTURING" },
      timestamp: new Date(Date.now() - 3600000 * 2 + 9000).toISOString()
    },
    {
      agent_name: "AuditingAgent",
      action: "SHA256_CRYPTOGRAPHIC_SEAL",
      status: "COMPLETED",
      duration_ms: 15,
      summary: "Generated immutable SHA-256 cryptographic digest for full case dossier",
      details: { hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" },
      timestamp: new Date(Date.now() - 3600000 * 2 + 10000).toISOString()
    }
  ],
  hypotheses: [
    {
      id: 1,
      hypothesis_id: "HYP_1",
      title: "Deliberate Structuring / Smurfing Scheme",
      description: "Customer intentionally splits a large $50,000 cash pool into sub-$10,000 deposits to evade Bank Secrecy Act CTR filing thresholds.",
      probability: 0.92,
      status: "SUPPORTED",
      corroborating_evidence: ["5 deposits between $9,200 and $9,950 within 4 hours", "Velocity Z-Score +4.82 sigma", "Shortest path to offshore intermediary: 2 hops"]
    }
  ],
  audit_logs: [
    {
      id: 1,
      case_id: "CASE_ALT_STRUCT_8821",
      actor: "RiskAssignmentAgent",
      action_type: "RISK_CALCULATED",
      description: "Calculated deterministic composite risk score = 92.5",
      execution_time_ms: 25.0,
      verification_hash: "a4f89d31b87c24ee18e7c10b784910248192a83912048f128912401824102841",
      timestamp: new Date(Date.now() - 3600000 * 2).toISOString()
    },
    {
      id: 2,
      case_id: "CASE_ALT_STRUCT_8821",
      actor: "AuditingAgent",
      action_type: "CASE_SEALED",
      description: "Case closed with decision BLOCK; cryptographic audit log finalized",
      execution_time_ms: 12.0,
      verification_hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      timestamp: new Date(Date.now() - 3600000 * 2 + 5000).toISOString()
    }
  ],
  feedback: []
};

export const INITIAL_MOCK_AUDIT_LOGS: AuditLogRow[] = [
  {
    id: 1,
    case_id: "CASE_ALT_STRUCT_8821",
    alert_id: "ALT_STRUCT_8821",
    actor: "Supervisor",
    action_type: "WORKFLOW_INITIATED",
    description: "Multi-agent LangGraph workflow initiated for alert ALT_STRUCT_8821",
    execution_time_ms: 45.0,
    verification_hash: "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
    timestamp: new Date(Date.now() - 3600000 * 2).toISOString()
  },
  {
    id: 2,
    case_id: "CASE_ALT_STRUCT_8821",
    alert_id: "ALT_STRUCT_8821",
    actor: "GraphRelationshipAgent",
    action_type: "NETWORK_TRAVERSAL",
    description: "Identified 2-hop linkage to high-risk counterparty ACC_CUST_0155_1",
    execution_time_ms: 215.0,
    verification_hash: "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
    timestamp: new Date(Date.now() - 3600000 * 2 + 2000).toISOString()
  },
  {
    id: 3,
    case_id: "CASE_ALT_STRUCT_8821",
    alert_id: "ALT_STRUCT_8821",
    actor: "RiskAssignmentAgent",
    action_type: "RISK_CALCULATED",
    description: "Computed deterministic risk score = 92.5 -> Band CRITICAL -> Decision BLOCK",
    execution_time_ms: 25.0,
    verification_hash: "a4f89d31b87c24ee18e7c10b784910248192a83912048f128912401824102841",
    timestamp: new Date(Date.now() - 3600000 * 2 + 4000).toISOString()
  },
  {
    id: 4,
    case_id: "CASE_ALT_STRUCT_8821",
    alert_id: "ALT_STRUCT_8821",
    actor: "RegulatoryReportingAgent",
    action_type: "SAR_DRAFTED",
    description: "FinCEN Suspicious Activity Report drafted and saved to case file",
    execution_time_ms: 140.0,
    verification_hash: "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
    timestamp: new Date(Date.now() - 3600000 * 2 + 6000).toISOString()
  }
];

export const INITIAL_MOCK_EVALUATION: EvaluationMetric = {
  run_id: "EVAL_8DA048D4",
  timestamp: new Date().toISOString(),
  split_type: "TEST",
  total_samples: 256,
  true_positives: 36,
  false_positives: 51,
  true_negatives: 169,
  false_negatives: 0,
  precision_score: 0.4138,
  recall_score: 1.0000,
  f1_score: 0.5854,
  accuracy_score: 0.8008,
  roc_auc: 0.9917,
  confusion_matrix_json: {
    true_positives: 36,
    false_positives: 51,
    true_negatives: 169,
    false_negatives: 0
  },
  classification_report_json: {
    "0": { "precision": 1.0, "recall": 0.77, "f1-score": 0.87, "support": 220 },
    "1": { "precision": 0.41, "recall": 1.0, "f1-score": 0.59, "support": 36 },
    "accuracy": 0.8008,
    "macro avg": { "precision": 0.71, "recall": 0.88, "f1-score": 0.73, "support": 256 },
    "weighted avg": { "precision": 0.92, "recall": 0.80, "f1-score": 0.83, "support": 256 }
  }
};
