import time
import datetime
from typing import Dict, Any
from app.agents.state import InvestigationState
from app.services.llm import llm_service


def report_sar_drafting_node(state: InvestigationState) -> InvestigationState:
    t0 = time.time()
    assembled = state.get("assembled_case", {})
    reasoning = state.get("reasoning_output", {})
    risk = state.get("risk_evaluation", {})

    sar_data = llm_service.draft_sar_report(assembled, reasoning, risk)

    # Generate rich markdown narrative
    score = risk.get("final_risk_score", 0.0)
    band = risk.get("final_risk_band", "LOW")
    decision = risk.get("final_decision", "ALLOW")
    cust = state.get("customer_data", {})
    alert = state.get("alert_data", {})

    report_markdown = f"""# SUSPICIOUS ACTIVITY REPORT (SAR / STR) — FORENSIC DRAFT
**Status:** DRAFT — REQUIRES COMPLIANCE OFFICER SIGN-OFF  
**Case ID:** {state.get('case_id')}  
**Alert ID:** {state.get('alert_id')}  
**Date Generated:** {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Investigation Mode:** {state.get('planner_mode', 'static').upper()}  
**Investigation Iterations:** {state.get('iteration_count', 1)}  

---

## 1. SUBJECT IDENTIFICATION
- **Legal Name / Entity:** {sar_data.get('subject_name')}
- **Customer Identifier:** {sar_data.get('subject_id')}
- **Declared Occupation / Business:** {cust.get('occupation', 'N/A')}
- **Country of Registration:** {cust.get('country', 'N/A')}
- **Risk Classification:** {cust.get('risk_tier', 'MEDIUM')} (PEP: {cust.get('is_pep', False)}, Sanctioned: {cust.get('is_sanctioned', False)})

---

## 2. SUSPICIOUS ACTIVITY OVERVIEW
- **Primary Alert Typology:** {sar_data.get('alert_type')}
- **Deterministic Risk Score:** **{score:.1f} / 100 ({band})**
- **Recommended Policy Action:** **{decision}**
- **Law Enforcement Referral:** {'RECOMMENDED' if sar_data.get('law_enforcement_referral_recommended') else 'NOT REQUIRED AT THIS STAGE'}

### Executive Summary
{sar_data.get('executive_summary')}

---

## 3. FORENSIC TRANSACTION NARRATIVE
{sar_data.get('suspicious_activity_narrative')}

---

## 4. NEXUS, NETWORK TOPOLOGY & METHODOLOGY
{sar_data.get('nexus_and_methodology')}

---

## 5. COMPLIANCE SIGN-OFF DISCLAIMER
> *This automated draft was synthesized by the SentinelGraph Multi-Agent Investigation Framework. In accordance with AML / BSA compliance regulations, final disposition and statutory reporting filings must be reviewed and authorized by a designated AML Compliance Officer.*
"""

    sar_data["formatted_markdown_report"] = report_markdown

    duration_ms = round((time.time() - t0) * 1000, 2)
    step_record = {
        "agent_name": "ReportSARDraftingAgent",
        "action": "SAR_REPORT_DRAFTED",
        "status": "COMPLETED",
        "duration_ms": duration_ms,
        "summary": f"Drafted FinCEN-standard SAR report for subject {sar_data.get('subject_name')}. Recommended Action: {decision}.",
        "details": sar_data,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    state["sar_report"] = sar_data
    state["agent_trail"].append(step_record)
    return state
