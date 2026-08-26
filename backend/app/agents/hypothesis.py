import time
import datetime
from typing import Dict, Any, List
from app.agents.state import InvestigationState
from app.services.llm import llm_service


def hypothesis_node(state: InvestigationState) -> InvestigationState:
    t0 = time.time()
    alert = state.get("alert_data", {})
    customer = state.get("customer_data", {})

    hypotheses = llm_service.generate_hypotheses(alert, customer)

    duration_ms = round((time.time() - t0) * 1000, 2)
    step_record = {
        "agent_name": "HypothesisGenerationAgent",
        "action": "HYPOTHESES_FORMULATED",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "summary": f"Formulated {len(hypotheses)} competing hypotheses to guide evidence retrieval.",
        "details": {"hypotheses": hypotheses},
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    state["hypotheses"] = hypotheses
    state["agent_trail"].append(step_record)
    return state
