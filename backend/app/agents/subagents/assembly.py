import time
import datetime
from typing import Dict, Any
from app.agents.state import InvestigationState


def case_assembly_node(state: InvestigationState) -> InvestigationState:
    t0 = time.time()
    alert = state.get("alert_data", {})
    cust = state.get("customer_data", {})
    evidence = state.get("evidence_data", {})
    graph = state.get("graph_data", {})
    behavior = state.get("behavior_data", {})
    doc = state.get("document_data", {})
    intel = state.get("intelligence_data", {})
    hypotheses = state.get("hypotheses", [])

    assembled_case = {
        "case_id": state.get("case_id"),
        "alert": alert,
        "customer": cust,
        "evidence": evidence,
        "graph_data": graph,
        "behavior_data": behavior,
        "document_data": doc,
        "intelligence_data": intel,
        "hypotheses": hypotheses,
        "assembly_timestamp": datetime.datetime.utcnow().isoformat()
    }

    duration_ms = round((time.time() - t0) * 1000, 2)
    step_record = {
        "agent_name": "CaseAssemblyAgent",
        "action": "CASE_ASSEMBLED",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "summary": "Consolidated evidence from 5 sub-agents and formulated unified forensic case dossier.",
        "details": {
            "evidence_keys": list(assembled_case.keys()),
            "total_transactions": evidence.get("total_transactions_analyzed", 0),
            "counterparties": graph.get("total_counterparties", 0),
            "intel_hits": intel.get("total_watchlist_hits", 0)
        },
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    state["assembled_case"] = assembled_case
    state["agent_trail"].append(step_record)
    return state
