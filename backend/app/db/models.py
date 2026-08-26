import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(64), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    risk_tier = Column(String(32), default="MEDIUM")  # LOW, MEDIUM, HIGH
    kyc_status = Column(String(32), default="VERIFIED")  # VERIFIED, PENDING, REJECTED
    occupation = Column(String(128), default="Professional")
    country = Column(String(64), default="US")
    is_pep = Column(Boolean, default=False)
    is_sanctioned = Column(Boolean, default=False)
    kyc_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    accounts = relationship("Account", back_populates="customer")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(64), unique=True, index=True, nullable=False)
    customer_id = Column(String(64), ForeignKey("customers.customer_id"), nullable=False)
    account_type = Column(String(32), default="CHECKING")  # SAVINGS, CHECKING, BUSINESS
    balance = Column(Float, default=10000.0)
    currency = Column(String(8), default="USD")
    opened_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(32), default="ACTIVE")  # ACTIVE, FROZEN, CLOSED

    customer = relationship("Customer", back_populates="accounts")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    txn_id = Column(String(64), unique=True, index=True, nullable=False)
    sender_account_id = Column(String(64), ForeignKey("accounts.account_id"), nullable=False)
    receiver_account_id = Column(String(64), ForeignKey("accounts.account_id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="USD")
    txn_type = Column(String(32), default="WIRE")  # WIRE, ACH, CASH_DEPOSIT, CARD, INTERNAL
    channel = Column(String(32), default="ONLINE")  # ONLINE, ATM, BRANCH, API
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    is_fraud_injected = Column(Boolean, default=False, index=True)
    fraud_pattern_type = Column(String(64), default="NONE")  # STRUCTURING, LAYERING, SMURFING, MULE, VELOCITY, NONE


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(64), unique=True, index=True, nullable=False)
    entity_type = Column(String(32), default="TRANSACTION")  # TRANSACTION, ACCOUNT, CUSTOMER
    entity_id = Column(String(64), nullable=False, index=True)
    alert_type = Column(String(64), nullable=False, index=True)  # STRUCTURING, LAYERING, SMURFING, MULE_ACCOUNT, VELOCITY_ABUSE, ISOLATION_FOREST
    severity = Column(String(32), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    raw_score = Column(Float, default=50.0)
    priority_rank = Column(Integer, default=1, index=True)
    status = Column(String(32), default="PENDING", index=True)  # PENDING, TRIAGED, INVESTIGATING, CLOSED, ESCALATED
    trigger_reason = Column(Text, nullable=False)
    features_json = Column(JSON, nullable=True)
    split_type = Column(String(16), default="TRAIN", index=True)  # TRAIN, TEST
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    triaged_at = Column(DateTime, nullable=True)

    investigation = relationship("InvestigationCase", back_populates="alert", uselist=False)


class InvestigationCase(Base):
    __tablename__ = "investigation_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), unique=True, index=True, nullable=False)
    alert_id = Column(String(64), ForeignKey("alerts.alert_id"), nullable=False)
    planner_mode = Column(String(32), default="static")  # static, adaptive
    status = Column(String(32), default="IN_PROGRESS", index=True)  # IN_PROGRESS, COMPLETED, FAILED
    iterations_count = Column(Integer, default=1)
    
    # Deterministic Risk Assignment Outputs
    final_risk_score = Column(Float, default=0.0)
    final_risk_band = Column(String(32), default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    final_decision = Column(String(32), default="ALLOW")  # ALLOW, REVIEW, BLOCK
    decision_rationale = Column(Text, nullable=True)
    
    # Multi-Agent Outputs
    plan_json = Column(JSON, nullable=True)
    hypotheses_json = Column(JSON, nullable=True)
    subagent_evidence_json = Column(JSON, nullable=True)
    reasoning_json = Column(JSON, nullable=True)
    sar_report_text = Column(Text, nullable=True)
    sar_narrative_json = Column(JSON, nullable=True)
    agent_trail_json = Column(JSON, nullable=True)  # chronological list of all agent steps
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    alert = relationship("Alert", back_populates="investigation")
    evidence_items = relationship("EvidenceItem", back_populates="case", cascade="all, delete-orphan")
    hypotheses = relationship("Hypothesis", back_populates="case", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="case", cascade="all, delete-orphan")
    feedback = relationship("InvestigatorFeedback", back_populates="case", cascade="all, delete-orphan")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("investigation_cases.case_id"), nullable=False)
    agent_name = Column(String(64), nullable=False)
    evidence_type = Column(String(64), nullable=False)  # TRANSACTION_HISTORY, GRAPH_TOPOLOGY, BEHAVIOR_STATS, KYC_DOCUMENTS, EXTERNAL_INTELLIGENCE
    data_json = Column(JSON, nullable=False)
    confidence_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    case = relationship("InvestigationCase", back_populates="evidence_items")


class Hypothesis(Base):
    __tablename__ = "hypotheses"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("investigation_cases.case_id"), nullable=False)
    hypothesis_id = Column(String(32), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    probability = Column(Float, default=0.5)
    status = Column(String(32), default="INCONCLUSIVE")  # SUPPORTED, REFUTED, INCONCLUSIVE
    corroborating_evidence = Column(JSON, nullable=True)
    contradicting_evidence = Column(JSON, nullable=True)

    case = relationship("InvestigationCase", back_populates="hypotheses")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("investigation_cases.case_id"), nullable=True, index=True)
    alert_id = Column(String(64), nullable=True, index=True)
    actor = Column(String(64), nullable=False, index=True)  # Supervisor, EvidenceRetrievalAgent, RiskAssignmentAgent, etc.
    action_type = Column(String(64), nullable=False, index=True)  # PLAN_GENERATED, EVIDENCE_COLLECTED, RISK_CALCULATED, etc.
    description = Column(Text, nullable=False)
    input_payload = Column(JSON, nullable=True)
    output_payload = Column(JSON, nullable=True)
    execution_time_ms = Column(Float, default=0.0)
    verification_hash = Column(String(64), nullable=False)  # SHA-256 immutable digest
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    case = relationship("InvestigationCase", back_populates="audit_logs")


class InvestigatorFeedback(Base):
    __tablename__ = "investigator_feedback"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("investigation_cases.case_id"), nullable=False)
    investigator_id = Column(String(64), default="analyst_default")
    feedback_type = Column(String(32), nullable=False)  # AGREE, DISAGREE, OVERRIDE, FALSE_POSITIVE, POLICY_ADJUSTMENT
    notes = Column(Text, nullable=False)
    adjusted_decision = Column(String(32), nullable=True)  # ALLOW, REVIEW, BLOCK
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    case = relationship("InvestigationCase", back_populates="feedback")


class EvaluationMetricRecord(Base):
    __tablename__ = "evaluation_metrics"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(64), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    split_type = Column(String(16), default="TEST")
    total_samples = Column(Integer, nullable=False)
    true_positives = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    true_negatives = Column(Integer, default=0)
    false_negatives = Column(Integer, default=0)
    precision_score = Column(Float, nullable=False)
    recall_score = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    accuracy_score = Column(Float, nullable=False)
    roc_auc = Column(Float, nullable=False)
    confusion_matrix_json = Column(JSON, nullable=False)
    classification_report_json = Column(JSON, nullable=False)
