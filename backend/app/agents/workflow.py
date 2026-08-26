import logging
import datetime
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import InvestigationState
from app.agents.supervisor import supervisor_node
from app.agents.planner import planner_node
from app.agents.hypothesis import hypothesis_node
from app.agents.subagents.evidence import evidence_retrieval_node
from app.agents.subagents.graph import graph_relationship_node
from app.agents.subagents.behavior import behavior_analysis_node
from app.agents.subagents.document import document_analysis_node
from app.agents.subagents.intelligence import external_intelligence_node
from app.agents.subagents.assembly import case_assembly_node
from app.agents.reasoning import reasoning_node
from app.agents.risk_scoring import risk_scoring_node
from app.agents.auditing import auditing_node
from app.agents.report_drafter import report_sar_drafting_node
from app.config import settings

from app.db.session import SessionLocal
from app.db.models import (
    InvestigationCase,
    Alert,
    EvidenceItem,
    Hypothesis,
    AuditLog,
    Customer
)

logger = logging.getLogger(__name__)


def should_loop_back(state: InvestigationState) -> Literal["supervisor", "risk_scoring"]:
    """Conditional Edge: evaluates if iterative re-investigation loop is required."""
    needs_more = state.get("needs_more_evidence", False)
    iterations = state.get("iteration_count", 1)
    
    if needs_more and iterations < settings.MAX_INVESTIGATION_LOOPS:
        logger.info(f"Triggering LangGraph loop-back to Supervisor (Iteration {iterations} -> {iterations + 1})")
        return "supervisor"
    return "risk_scoring"


def build_investigation_graph():
    builder = StateGraph(InvestigationState)

    # 1. Add all 12 distinct functional nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("planner", planner_node)
    builder.add_node("hypothesis", hypothesis_node)
    builder.add_node("evidence_retrieval", evidence_retrieval_node)
    builder.add_node("graph_relationship", graph_relationship_node)
    builder.add_node("behavior_analysis", behavior_analysis_node)
    builder.add_node("document_analysis", document_analysis_node)
    builder.add_node("external_intelligence", external_intelligence_node)
    builder.add_node("case_assembly", case_assembly_node)
    builder.add_node("reasoning", reasoning_node)
    builder.add_node("risk_scoring", risk_scoring_node)
    builder.add_node("auditing", auditing_node)
    builder.add_node("report_drafter", report_sar_drafting_node)

    # 2. Sequential & Parallel Flow Edges
    builder.add_edge(START, "supervisor")
    builder.add_edge("supervisor", "planner")
    builder.add_edge("planner", "hypothesis")
    builder.add_edge("hypothesis", "evidence_retrieval")
    builder.add_edge("evidence_retrieval", "graph_relationship")
    builder.add_edge("graph_relationship", "behavior_analysis")
    builder.add_edge("behavior_analysis", "document_analysis")
    builder.add_edge("document_analysis", "external_intelligence")
    builder.add_edge("external_intelligence", "case_assembly")
    builder.add_edge("case_assembly", "reasoning")

    # 3. Conditional Loop-Back Edge (max 2 cycles)
    builder.add_conditional_edges(
        "reasoning",
        should_loop_back,
        {
            "supervisor": "supervisor",
            "risk_scoring": "risk_scoring"
        }
    )

    # 4. Governance & Outcomes
    builder.add_edge("risk_scoring", "auditing")
    builder.add_edge("auditing", "report_drafter")
    builder.add_edge("report_drafter", END)

    # Memory Checkpointing
    memory = MemorySaver()
    return builder.compile(checkpointer=memory)


compiled_investigation_graph = build_investigation_graph()


def execute_investigation_case(
    case_id: str,
    alert_id: str,
    planner_mode: str = "static"
) -> Dict[str, Any]:
    """
    Executes a complete multi-agent investigation run via LangGraph and persists results to PostgreSQL.
    """
    # 1. Fetch initial alert & customer details in a cleanly isolated transaction
    db = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
        if not alert:
            raise ValueError(f"Alert {alert_id} not found.")

        cust_id = alert.features_json.get("customer_id") if alert.features_json else None
        cust_record = None
        if cust_id:
            cust_record = db.query(Customer).filter(Customer.customer_id == cust_id).first()

        customer_data = {
            "customer_id": cust_record.customer_id if cust_record else "CUST_DEFAULT",
            "full_name": cust_record.full_name if cust_record else "Subject Entity",
            "risk_tier": cust_record.risk_tier if cust_record else "MEDIUM",
            "occupation": cust_record.occupation if cust_record else "Business Owner",
            "country": cust_record.country if cust_record else "US",
            "is_pep": cust_record.is_pep if cust_record else False,
            "is_sanctioned": cust_record.is_sanctioned if cust_record else False,
            "kyc_notes": cust_record.kyc_notes if cust_record else "Standard KYC documentation on file."
        }

        alert_data = {
            "alert_id": alert.alert_id,
            "entity_type": alert.entity_type,
            "entity_id": alert.entity_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "raw_score": alert.raw_score,
            "trigger_reason": alert.trigger_reason,
            "features_json": alert.features_json or {}
        }
    finally:
        db.close()

    # 2. Run LangGraph Multi-Agent Investigation
    initial_state: InvestigationState = {
        "case_id": case_id,
        "alert_id": alert_id,
        "alert_data": alert_data,
        "customer_data": customer_data,
        "planner_mode": planner_mode,
        "plan": {},
        "hypotheses": [],
        "evidence_data": {},
        "graph_data": {},
        "behavior_data": {},
        "document_data": {},
        "intelligence_data": {},
        "assembled_case": {},
        "reasoning_output": {},
        "risk_evaluation": {},
        "sar_report": {},
        "iteration_count": 0,
        "needs_more_evidence": False,
        "missing_evidence_reasons": [],
        "agent_trail": [],
        "audit_logs": []
    }

    config = {"configurable": {"thread_id": case_id}}
    final_state = compiled_investigation_graph.invoke(initial_state, config)

    # 3. Persist Final Investigation Dossier, Risk Score & SAR Report to DB
    db = SessionLocal()
    try:
        alert_obj = db.query(Alert).filter(Alert.alert_id == alert_id).first()
        risk_eval = final_state.get("risk_evaluation", {})
        sar_res = final_state.get("sar_report", {})

        case_obj = db.query(InvestigationCase).filter(InvestigationCase.case_id == case_id).first()
        if not case_obj:
            case_obj = InvestigationCase(
                case_id=case_id,
                alert_id=alert_id,
                planner_mode=planner_mode
            )
            db.add(case_obj)

        case_obj.status = "COMPLETED"
        case_obj.iterations_count = final_state.get("iteration_count", 1)
        case_obj.final_risk_score = risk_eval.get("final_risk_score", 0.0)
        case_obj.final_risk_band = risk_eval.get("final_risk_band", "LOW")
        case_obj.final_decision = risk_eval.get("final_decision", "ALLOW")
        case_obj.decision_rationale = risk_eval.get("decision_rationale", "")
        case_obj.plan_json = final_state.get("plan")
        case_obj.hypotheses_json = final_state.get("hypotheses")
        case_obj.subagent_evidence_json = {
            "evidence_data": final_state.get("evidence_data"),
            "graph_data": final_state.get("graph_data"),
            "behavior_data": final_state.get("behavior_data"),
            "document_data": final_state.get("document_data"),
            "intelligence_data": final_state.get("intelligence_data"),
            "assembled_case": final_state.get("assembled_case")
        }
        case_obj.reasoning_json = final_state.get("reasoning_output")
        case_obj.sar_report_text = sar_res.get("formatted_markdown_report")
        case_obj.sar_narrative_json = sar_res
        case_obj.agent_trail_json = final_state.get("agent_trail")
        case_obj.completed_at = datetime.datetime.utcnow()

        if alert_obj:
            alert_obj.status = "INVESTIGATING" if case_obj.final_decision == "REVIEW" else ("CLOSED" if case_obj.final_decision == "ALLOW" else "ESCALATED")

        # Save Evidence Items
        for ev_type, ev_val in [
            ("TRANSACTION_HISTORY", final_state.get("evidence_data")),
            ("GRAPH_TOPOLOGY", final_state.get("graph_data")),
            ("BEHAVIOR_STATS", final_state.get("behavior_data")),
            ("KYC_DOCUMENTS", final_state.get("document_data")),
            ("EXTERNAL_INTELLIGENCE", final_state.get("intelligence_data"))
        ]:
            if ev_val:
                db.add(EvidenceItem(
                    case_id=case_id,
                    agent_name=ev_type,
                    evidence_type=ev_type,
                    data_json=ev_val,
                    confidence_score=1.0
                ))

        # Save Hypotheses
        for h in final_state.get("hypotheses", []):
            db.add(Hypothesis(
                case_id=case_id,
                hypothesis_id=h.get("hypothesis_id", "H0"),
                title=h.get("title", "Hypothesis"),
                description=h.get("description", ""),
                probability=h.get("probability", 0.5),
                status=h.get("status", "INCONCLUSIVE"),
                corroborating_evidence=h.get("corroborating_evidence", []),
                contradicting_evidence=h.get("contradicting_evidence", [])
            ))

        # Save Audit Logs
        for a_log in final_state.get("audit_logs", []):
            db.add(AuditLog(
                case_id=case_id,
                alert_id=alert_id,
                actor=a_log.get("actor", "Unknown"),
                action_type=a_log.get("action_type", "ACTION"),
                description=a_log.get("description", ""),
                input_payload=a_log.get("input_payload"),
                output_payload=a_log.get("output_payload"),
                execution_time_ms=a_log.get("execution_time_ms", 0.0),
                verification_hash=a_log.get("verification_hash", "0000000000000000")
            ))

        db.commit()
        return final_state
    finally:
        db.close()
