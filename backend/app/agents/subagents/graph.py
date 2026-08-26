import time
import datetime
from typing import Dict, Any
from app.agents.state import InvestigationState
from app.services.graph_store import financial_graph_store
from app.db.session import SessionLocal


def graph_relationship_node(state: InvestigationState) -> InvestigationState:
    t0 = time.time()
    alert = state.get("alert_data", {})
    entity_id = alert.get("entity_id", "")
    evidence = state.get("evidence_data", {})
    target_accs = evidence.get("target_account_ids", [entity_id])
    primary_acc = target_accs[0] if target_accs else entity_id

    db = SessionLocal()
    try:
        financial_graph_store.build_graph(db)
        graph_analysis = financial_graph_store.analyze_entity_subgraph(primary_acc, max_hops=2)
    finally:
        db.close()

    duration_ms = round((time.time() - t0) * 1000, 2)
    step_record = {
        "agent_name": "GraphRelationshipAgent",
        "action": "GRAPH_TRAVERSED",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "summary": (
            f"Analyzed 2-hop network graph: {graph_analysis['total_counterparties']} counterparties, "
            f"{graph_analysis['high_risk_connections_count']} high-risk connections. "
            f"Path to watchlist: {graph_analysis['shortest_path_to_watchlist']}."
        ),
        "details": graph_analysis,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    state["graph_data"] = graph_analysis
    state["agent_trail"].append(step_record)
    return state
