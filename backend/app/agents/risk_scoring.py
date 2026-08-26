import time
import datetime
from typing import Dict, Any, Tuple
from app.agents.state import InvestigationState
from app.config import settings


def compute_deterministic_risk_score(
    alert_raw_score: float,
    graph_data: Dict[str, Any],
    behavior_data: Dict[str, Any],
    intel_data: Dict[str, Any],
    doc_data: Dict[str, Any]
) -> Tuple[float, str, str, str, Dict[str, float]]:
    """
    Deterministic Python Risk Assignment Engine.
    Strictly mathematical, auditable, and rule-bounded (Zero LLM hallucinations).
    """
    # 1. Raw Alert Signal (0 - 100)
    s_raw = min(100.0, max(0.0, float(alert_raw_score)))

    # 2. Graph Risk Component (0 - 100)
    hr_hops = graph_data.get("high_risk_connections_count", 0)
    has_cycles = 1.0 if graph_data.get("has_cycles", False) else 0.0
    deg_cent = min(1.0, float(graph_data.get("degree_centrality", 0.0)) * 5)
    s_graph = min(100.0, (hr_hops * 35.0) + (has_cycles * 25.0) + (deg_cent * 20.0))

    # 3. Behavioral Anomaly Component (0 - 100)
    vel_z = max(0.0, float(behavior_data.get("velocity_z_score", 0.0)))
    amt_z = max(0.0, float(behavior_data.get("amount_z_score", 0.0)))
    out_ratio = max(0.0, min(1.0, float(behavior_data.get("outbound_ratio", 0.5))))
    s_behavior = min(100.0, (vel_z * 15.0) + (amt_z * 12.0) + (out_ratio * 30.0))

    # 4. External Intelligence Component (0 - 100)
    s_intel = min(100.0, float(intel_data.get("intelligence_risk_score", 0.0)))

    # 5. Document Risk Component (0 - 100)
    s_doc = min(100.0, float(doc_data.get("document_risk_score", 15.0)))

    # Multi-Factor Weighted Combination
    # Weights: Raw Alert (25%), Graph (25%), Behavior (20%), Intel (20%), Docs (10%)
    w_raw = 0.25
    w_graph = 0.25
    w_behavior = 0.20
    w_intel = 0.20
    w_doc = 0.10

    weighted_score = (
        (w_raw * s_raw) +
        (w_graph * s_graph) +
        (w_behavior * s_behavior) +
        (w_intel * s_intel) +
        (w_doc * s_doc)
    )

    final_score = round(min(100.0, max(0.0, weighted_score)), 1)

    # Risk Band Assignment
    if final_score <= settings.RISK_BAND_LOW_MAX:
        band = "LOW"
    elif final_score <= settings.RISK_BAND_MEDIUM_MAX:
        band = "MEDIUM"
    elif final_score <= settings.RISK_BAND_HIGH_MAX:
        band = "HIGH"
    else:
        band = "CRITICAL"

    # Decision Policy Assignment
    if final_score <= settings.DECISION_ALLOW_MAX:
        decision = "ALLOW"
    elif final_score <= settings.DECISION_REVIEW_MAX:
        decision = "REVIEW"
    else:
        decision = "BLOCK"

    rationale = (
        f"Deterministic risk evaluation computed composite score of {final_score:.1f}/100 ({band}) "
        f"via weighted features: Raw Alert ({s_raw:.1f} × {w_raw}), Graph Network ({s_graph:.1f} × {w_graph}), "
        f"Behavioral Outlier ({s_behavior:.1f} × {w_behavior}), Watchlist Intel ({s_intel:.1f} × {w_intel}), "
        f"KYC Document Flags ({s_doc:.1f} × {w_doc}). Recommended policy action: {decision}."
    )

    breakdown = {
        "raw_alert_score": round(s_raw, 1),
        "graph_risk_score": round(s_graph, 1),
        "behavior_risk_score": round(s_behavior, 1),
        "intel_risk_score": round(s_intel, 1),
        "doc_risk_score": round(s_doc, 1)
    }

    return final_score, band, decision, rationale, breakdown


def risk_scoring_node(state: InvestigationState) -> InvestigationState:
    t0 = time.time()
    alert = state.get("alert_data", {})
    graph = state.get("graph_data", {})
    behavior = state.get("behavior_data", {})
    intel = state.get("intelligence_data", {})
    doc = state.get("document_data", {})

    raw_score = alert.get("raw_score", 50.0)
    score, band, decision, rationale, breakdown = compute_deterministic_risk_score(
        raw_score, graph, behavior, intel, doc
    )

    risk_evaluation = {
        "final_risk_score": score,
        "final_risk_band": band,
        "final_decision": decision,
        "decision_rationale": rationale,
        "feature_score_breakdown": breakdown,
        "is_deterministic": True
    }

    duration_ms = round((time.time() - t0) * 1000, 2)
    step_record = {
        "agent_name": "RiskAssignmentAgent (Deterministic Python)",
        "action": "RISK_CALCULATED",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "summary": f"Calculated deterministic risk score: {score:.1f}/100 [{band}] -> Action: {decision}.",
        "details": risk_evaluation,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    state["risk_evaluation"] = risk_evaluation
    state["agent_trail"].append(step_record)
    return state
