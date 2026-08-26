import time
import datetime
from typing import Dict, Any
from app.agents.state import InvestigationState


def document_analysis_node(state: InvestigationState) -> InvestigationState:
    t0 = time.time()
    cust = state.get("customer_data", {})
    kyc_notes = cust.get("kyc_notes", "Standard KYC verification completed.")
    occupation = cust.get("occupation", "Professional")
    risk_tier = cust.get("risk_tier", "LOW")

    # Document text parsing & risk flags
    has_enhanced_due_diligence = "Enhanced Due Diligence" in kyc_notes
    has_periodic_review_flag = "periodic review" in kyc_notes
    source_declared = "business revenue" in kyc_notes.lower() or "import/export" in kyc_notes.lower()

    doc_risk_score = 15.0
    if has_periodic_review_flag:
        doc_risk_score += 35.0
    if risk_tier == "HIGH":
        doc_risk_score += 30.0

    doc_analysis = {
        "raw_kyc_notes": kyc_notes,
        "declared_occupation": occupation,
        "source_of_funds_verified": source_declared,
        "enhanced_due_diligence_completed": has_enhanced_due_diligence,
        "periodic_review_flags": has_periodic_review_flag,
        "document_risk_score": min(100.0, doc_risk_score),
        "extracted_entities": [occupation, cust.get("country", "US")]
    }

    duration_ms = round((time.time() - t0) * 1000, 2)
    step_record = {
        "agent_name": "DocumentAnalysisAgent",
        "action": "DOCUMENTS_PARSED",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "summary": f"Parsed KYC notes & occupation ({occupation}). Document risk score: {doc_analysis['document_risk_score']:.1f}/100.",
        "details": doc_analysis,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    state["document_data"] = doc_analysis
    state["agent_trail"].append(step_record)
    return state
