import time
import datetime
from typing import Dict, Any
from app.agents.state import InvestigationState
from app.services.llm import llm_service
from app.config import settings


def reasoning_node(state: InvestigationState) -> InvestigationState:
    t0 = time.time()
    assembled = state.get("assembled_case", {})
    hypotheses = state.get("hypotheses", [])
    iteration = state.get("iteration_count", 1)

    reasoning_res = llm_service.analyze_and_reason(assembled, hypotheses, iteration)

    # Evaluate loop-back conditions
    confidence = reasoning_res.get("confidence_score", 0.85)
    needs_more = reasoning_res.get("needs_more_evidence", False)
    
    # Loop condition: only loop if flagged, confidence low, and iteration < MAX_INVESTIGATION_LOOPS
    if needs_more and iteration < settings.MAX_INVESTIGATION_LOOPS:
        state["needs_more_evidence"] = True
        state["missing_evidence_reasons"] = reasoning_res.get("missing_evidence_reasons", ["Additional counterparty screening required."])
    else:
        state["needs_more_evidence"] = False
        state["missing_evidence_reasons"] = []

    duration_ms = round((time.time() - t0) * 1000, 2)
    step_record = {
        "agent_name": f"AnalysisReasoningAgent (Iteration {iteration})",
        "action": "EVIDENCE_SYNTHESIZED",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "summary": (
            f"Forensic synthesis completed (Confidence: {confidence:.2f}). "
            f"Loop-back required: {state['needs_more_evidence']}."
        ),
        "details": reasoning_res,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    state["reasoning_output"] = reasoning_res
    state["agent_trail"].append(step_record)
    return state
