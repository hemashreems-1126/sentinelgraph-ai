import time
import datetime
from typing import Dict, Any
from app.agents.state import InvestigationState


def supervisor_node(state: InvestigationState) -> InvestigationState:
    t0 = time.time()
    iter_count = state.get("iteration_count", 0) + 1
    state["iteration_count"] = iter_count
    
    alert = state.get("alert_data", {})
    alert_type = alert.get("alert_type", "ANOMALY")
    planner_mode = state.get("planner_mode", "static")
    
    if iter_count == 1:
        summary_msg = f"Supervisor initiated investigation for {alert_type} ({alert.get('alert_id')}) using {planner_mode} planner."
    else:
        reasons = state.get("missing_evidence_reasons", [])
        summary_msg = f"Supervisor executing loop-back re-investigation (Cycle {iter_count}). Focus directives: {', '.join(reasons)}."

    duration_ms = round((time.time() - t0) * 1000, 2)
    step_record = {
        "agent_name": f"SupervisorAgent (Cycle {iter_count})",
        "action": "WORKFLOW_ORCHESTRATED",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "summary": summary_msg,
        "details": {
            "iteration": iter_count,
            "planner_mode": planner_mode,
            "alert_type": alert_type
        },
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    if "agent_trail" not in state:
        state["agent_trail"] = []
    state["agent_trail"].append(step_record)
    return state
