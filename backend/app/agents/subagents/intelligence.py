import time
import datetime
from typing import Dict, Any
from app.agents.state import InvestigationState


def external_intelligence_node(state: InvestigationState) -> InvestigationState:
    t0 = time.time()
    cust = state.get("customer_data", {})
    cust_name = cust.get("full_name", "Subject")
    is_pep = cust.get("is_pep", False)
    is_sanctioned = cust.get("is_sanctioned", False)
    country = cust.get("country", "US")

    # MOCKED External Intelligence (PEP, OFAC Sanctions, Adverse Media)
    # Clearly documented as synthetic mock in accordance with specification.
    matches = []
    intel_risk_score = 0.0

    if is_sanctioned:
        matches.append({
            "source": "OFAC SDN Register (MOCK)",
            "match_type": "EXACT_SANCTION_MATCH",
            "score": 0.99,
            "details": f"Subject {cust_name} matches SDN designation list #SDN-994281."
        })
        intel_risk_score += 75.0

    if is_pep:
        matches.append({
            "source": "Global PEP Register (MOCK)",
            "match_type": "POLITICALLY_EXPOSED_PERSON",
            "score": 0.92,
            "details": f"Subject {cust_name} identified as senior official/relative in {country} jurisdiction."
        })
        intel_risk_score += 45.0

    # Adverse media mock simulation
    if "Jewelry" in cust.get("occupation", "") or "Crypto" in cust.get("occupation", ""):
        matches.append({
            "source": "Adverse Media Newsfeed (MOCK)",
            "match_type": "HIGH_RISK_INDUSTRY_ALERT",
            "score": 0.70,
            "details": "Recent media investigations regarding unregulated OTC settlement intermediaries."
        })
        intel_risk_score += 20.0

    intel_risk_score = min(100.0, intel_risk_score)

    intel_data = {
        "is_mocked_feed": True,
        "screened": True,
        "subject_name": cust_name,
        "sanctions_match": is_sanctioned,
        "pep_match": is_pep,
        "total_watchlist_hits": len(matches),
        "matches": matches,
        "flag_summary": f"{len(matches)} intelligence hits (Sanctions: {is_sanctioned}, PEP: {is_pep})",
        "intelligence_risk_score": intel_risk_score
    }

    duration_ms = round((time.time() - t0) * 1000, 2)
    step_record = {
        "agent_name": "ExternalIntelligenceAgent (Mocked)",
        "action": "INTELLIGENCE_SCREENED",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "summary": f"Screened PEP/Sanctions/Media (Mocked): {len(matches)} hits found. Intel risk score: {intel_risk_score:.1f}/100.",
        "details": intel_data,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    state["intelligence_data"] = intel_data
    state["agent_trail"].append(step_record)
    return state
