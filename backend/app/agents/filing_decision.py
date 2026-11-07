"""
Filing Decision Agent (deterministic, no LLM).

Answers the question the vendors skip: *should* this alert become an STR to FIU-IND?
  * FILE_STR  → with a severity tier so FIU-IND / the Principal Officer can prioritise
  * NO_FILE   → with a documented closure memo (a non-filing decision must be recorded
                as carefully as a filing decision)

Inputs: the deterministic risk score and the evidence-linked red flags from the fact sheet.
"""
import time
import datetime
from typing import Any, Dict, List

from app.agents.state import InvestigationState
from app.agents.fact_sheet import build_fact_sheet

# Policy thresholds — kept here so a compliance team can read and change them.
FILE_SCORE_THRESHOLD = 60.0      # HIGH / CRITICAL risk band (used for tiering)
STRONG_ALONE_SCORE = 75.0        # one strong red flag is enough only with a high risk score
TIER1_SCORE_THRESHOLD = 80.0


def decide_filing(risk_score: float, red_flags: List[Dict[str, Any]]) -> Dict[str, Any]:
    strong = [f for f in red_flags if f.get("strength") == "STRONG"]
    codes = {f["code"] for f in red_flags}

    moderate = [f for f in red_flags if f.get("strength") != "STRONG"]
    # Grounds of suspicion must rest on evidence, not on the score alone:
    #   two strong flags, or one strong flag corroborated by a moderate one, or one strong flag
    #   with a high risk score. Moderate flags alone (velocity, PEP, repeat alerts) never file.
    file_str = (
        "SANCTIONS_MATCH" in codes
        or len(strong) >= 2
        or (len(strong) == 1 and len(moderate) >= 1)
        or (len(strong) == 1 and risk_score >= STRONG_ALONE_SCORE)
    )

    if not file_str:
        reasons = []
        if not red_flags:
            reasons.append("No evidence-backed red flag was found in the suspicious window.")
        else:
            reasons.append(
                f"Only {len(red_flags)} red flag(s) found ({', '.join(sorted(codes))}), "
                f"none strong enough on their own to establish grounds of suspicion."
            )
        if not strong:
            reasons.append("No strong red flag (e.g. pass-through, many unrelated payers, cash just under "
                           "the PAN threshold, split payments) was found.")
        elif risk_score < STRONG_ALONE_SCORE:
            reasons.append("A single strong red flag without corroborating evidence and with a moderate risk "
                           "score is consistent with legitimate activity (e.g. a merchant or rent collection).")
        return {
            "decision": "NO_FILE",
            "tier": None,
            "reasons": reasons,
            "recommended_action": "Close the alert with this memo on file and continue routine monitoring. "
                                  "Re-open automatically if a new alert is raised on the same account.",
        }

    live_mule = {"RAPID_PASS_THROUGH", "MANY_UNRELATED_PAYERS"} <= codes
    if "SANCTIONS_MATCH" in codes or risk_score >= TIER1_SCORE_THRESHOLD or live_mule:
        tier = "TIER_1_URGENT"
        action = ("File the STR without delay and consider an immediate debit freeze/lien so "
                  "remaining funds can be traced back to victims.")
    elif risk_score >= FILE_SCORE_THRESHOLD or len(strong) >= 2:
        tier = "TIER_2_PRIORITY"
        action = "File the STR within the statutory timeline and place the account under enhanced monitoring."
    else:
        tier = "TIER_3_ROUTINE"
        action = "File the STR within the statutory timeline."

    reasons = [f"{f['code']}: {f['description']}" for f in red_flags]
    return {"decision": "FILE_STR", "tier": tier, "reasons": reasons, "recommended_action": action}


def filing_decision_node(state: InvestigationState) -> InvestigationState:
    t0 = time.time()
    fact_sheet = build_fact_sheet(state)
    risk = state.get("risk_evaluation", {})
    score = float(risk.get("final_risk_score", 0.0))

    decision = decide_filing(score, fact_sheet["red_flags"])
    decision["risk_score"] = score
    decision["red_flags"] = fact_sheet["red_flags"]

    state["fact_sheet"] = fact_sheet
    state["filing_decision"] = decision

    label = decision["decision"] + (f" ({decision['tier']})" if decision["tier"] else "")
    state["agent_trail"].append({
        "agent_name": "FilingDecisionAgent (Deterministic Python)",
        "action": "FILING_DECISION_MADE",
        "status": "COMPLETED",
        "duration_ms": round((time.time() - t0) * 1000, 2),
        "summary": f"Decision: {label}. {len(fact_sheet['red_flags'])} evidence-backed red flag(s); risk score {score:.1f}.",
        "details": decision,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    })
    return state
