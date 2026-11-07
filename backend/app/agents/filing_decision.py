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


# Short plain-English names for red flags, used in analyst-facing reasons.
FLAG_PLAIN = {
    "RAPID_PASS_THROUGH": "money passed straight through the account",
    "MANY_UNRELATED_PAYERS": "many first-time payers in one day",
    "CASH_BELOW_PAN_THRESHOLD": "cash deposits kept just under ₹50,000",
    "SPLIT_PAYMENTS_SAME_BENEFICIARY": "repeated split payments to one person",
    "HIGH_VELOCITY": "a quick burst of transactions",
    "BEHAVIOUR_OUTLIER": "activity unusual for this account",
    "ONWARD_LAYERING": "the next account passed the money on too",
    "DORMANT_ACCOUNT_ACTIVATED": "a quiet account suddenly became busy",
    "NEW_ACCOUNT_HIGH_ACTIVITY": "a new account moving money for others",
    "PERSONAL_ACCOUNT_COLLECTION": "a personal account collecting from many people",
    "CIRCULAR_FLOW": "money going round in a circle",
    "REPEAT_ALERTS": "earlier alerts on the same account",
    "PEP_MATCH": "a politically exposed person",
    "SANCTIONS_MATCH": "a sanctions-list match",
}


def plain(code: str) -> str:
    return FLAG_PLAIN.get(code, code.replace("_", " ").lower())


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
            reasons.append("No suspicious pattern was confirmed in the transactions around this alert.")
        else:
            found = "; ".join(plain(f["code"]) for f in red_flags)
            reasons.append(f"Only weaker signs were found ({found}).")
        if not strong:
            reasons.append("None of the strong warning signs (money passed straight through, many first-time "
                           "payers, cash just under ₹50,000, split payments) is present.")
        elif risk_score < STRONG_ALONE_SCORE:
            reasons.append("One warning sign on its own, with nothing to back it up, fits normal activity too — "
                           "for example a shop or friends splitting rent.")
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
