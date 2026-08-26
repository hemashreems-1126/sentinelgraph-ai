import time
import datetime
from typing import Dict, Any
from app.agents.state import InvestigationState
from app.services.llm import llm_service


def get_static_checklist(alert_type: str, severity: str) -> Dict[str, Any]:
    """Deterministic checklist per alert type (Static Plan Default)."""
    if alert_type == "STRUCTURING":
        steps = [
            {"step": 1, "agent": "EvidenceRetrievalAgent", "task": "Extract 90-day cash deposit and wire transactions just below $10,000 threshold."},
            {"step": 2, "agent": "GraphRelationshipAgent", "task": "Identify sender and receiver accounts, check for common beneficiary connections."},
            {"step": 3, "agent": "BehaviorAnalysisAgent", "task": "Evaluate deposit frequency, weekend vs weekday patterns, and historical monthly turnover."},
            {"step": 4, "agent": "DocumentAnalysisAgent", "task": "Review customer KYC profile, occupation declaration, and stated source of wealth."},
            {"step": 5, "agent": "ExternalIntelligenceAgent", "task": "Screen customer against PEP, OFAC sanctions, and adverse media registers."},
            {"step": 6, "agent": "CaseAssemblyAgent", "task": "Consolidate structuring evidence into structured case file."}
        ]
    elif alert_type == "LAYERING":
        steps = [
            {"step": 1, "agent": "EvidenceRetrievalAgent", "task": "Retrieve end-to-end multi-hop transaction logs and timestamps."},
            {"step": 2, "agent": "GraphRelationshipAgent", "task": "Traverse 2-hop directed flow graph, calculate hop velocity and shell intermediary nodes."},
            {"step": 3, "agent": "BehaviorAnalysisAgent", "task": "Compute pass-through ratios (inbound vs outbound amounts and time delta)."},
            {"step": 4, "agent": "DocumentAnalysisAgent", "task": "Verify commercial business registration and counterparties' corporate nature."},
            {"step": 5, "agent": "ExternalIntelligenceAgent", "task": "Perform sanctions and watchlist check on all intermediate transit entities."},
            {"step": 6, "agent": "CaseAssemblyAgent", "task": "Assemble multi-hop flow timeline and network topology."}
        ]
    elif alert_type == "MULE_ACCOUNT":
        steps = [
            {"step": 1, "agent": "EvidenceRetrievalAgent", "task": "Fetch account open date, historical dormancy period, and sudden high-volume credits."},
            {"step": 2, "agent": "GraphRelationshipAgent", "task": "Examine origin of funds and immediate destination payout accounts."},
            {"step": 3, "agent": "BehaviorAnalysisAgent", "task": "Calculate account dormancy index and immediate fund dissipation velocity."},
            {"step": 4, "agent": "DocumentAnalysisAgent", "task": "Verify identity documentation, device login fingerprint changes, and contact updates."},
            {"step": 5, "agent": "ExternalIntelligenceAgent", "task": "Screen originator and ultimate recipient entities against watchlists."},
            {"step": 6, "agent": "CaseAssemblyAgent", "task": "Consolidate mule account risk profile."}
        ]
    elif alert_type == "VELOCITY_ABUSE":
        steps = [
            {"step": 1, "agent": "EvidenceRetrievalAgent", "task": "Extract microsecond transaction timestamps, API client IDs, and channel metadata."},
            {"step": 2, "agent": "GraphRelationshipAgent", "task": "Analyze fan-out / fan-in transaction graph density."},
            {"step": 3, "agent": "BehaviorAnalysisAgent", "task": "Calculate rolling 15-minute transaction velocity and z-score spike vs customer normal baseline."},
            {"step": 4, "agent": "DocumentAnalysisAgent", "task": "Review API integration contract and authorized volume thresholds."},
            {"step": 5, "agent": "ExternalIntelligenceAgent", "task": "Check IP / geolocation threat intelligence and watchlist hits."},
            {"step": 6, "agent": "CaseAssemblyAgent", "task": "Compile automated velocity abuse incident package."}
        ]
    else:
        steps = [
            {"step": 1, "agent": "EvidenceRetrievalAgent", "task": "Gather standard 90-day transaction history and account profiles."},
            {"step": 2, "agent": "GraphRelationshipAgent", "task": "Traverse 2-hop transaction network graph."},
            {"step": 3, "agent": "BehaviorAnalysisAgent", "task": "Calculate baseline volume and velocity deviation metrics."},
            {"step": 4, "agent": "DocumentAnalysisAgent", "task": "Parse KYC notes and occupation filings."},
            {"step": 5, "agent": "ExternalIntelligenceAgent", "task": "Run mock PEP and sanctions screening."},
            {"step": 6, "agent": "CaseAssemblyAgent", "task": "Assemble comprehensive investigation case."}
        ]

    return {
        "planner_mode": "static",
        "alert_type": alert_type,
        "primary_objective": f"Standard deterministic triage and evidence collection for {alert_type} ({severity}).",
        "required_data_sources": ["Transaction Ledger", "Entity Graph", "Behavioral Stats", "KYC Files", "Watchlists"],
        "planned_steps": steps,
        "adaptation_reason": "Deterministic compliance SOP execution."
    }


def planner_node(state: InvestigationState) -> InvestigationState:
    t0 = time.time()
    alert = state.get("alert_data", {})
    planner_mode = state.get("planner_mode", "static")
    alert_type = alert.get("alert_type", "ANOMALY")
    severity = alert.get("severity", "MEDIUM")

    if planner_mode == "adaptive":
        plan = llm_service.generate_adaptive_plan(alert, prior_evidence=state.get("evidence_data"))
    else:
        plan = get_static_checklist(alert_type, severity)

    duration_ms = round((time.time() - t0) * 1000, 2)
    step_record = {
        "agent_name": f"InvestigationPlanner ({planner_mode.capitalize()})",
        "action": "PLAN_GENERATED",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "summary": f"Generated {planner_mode} investigation plan with {len(plan.get('planned_steps', []))} mandatory steps.",
        "details": plan,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    state["plan"] = plan
    state["agent_trail"].append(step_record)
    return state
