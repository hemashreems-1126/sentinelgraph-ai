"""
Report Drafting Agent.

Builds either:
  * an FIU-IND style STR draft   (when the filing decision is FILE_STR), or
  * an alert closure memo        (when the decision is NO_FILE)

The body of both is a list of evidence-linked claims from the fact sheet. The LLM may
re-word those claims, but the Fact Checker re-verifies every one against the ledger
before the report can be approved.
"""
import time
import datetime
from typing import Any, Dict

from app.agents.state import InvestigationState
from app.services.llm import llm_service

TIER_LABELS = {
    "TIER_1_URGENT": "Tier 1 — Urgent",
    "TIER_2_PRIORITY": "Tier 2 — Priority",
    "TIER_3_ROUTINE": "Tier 3 — Routine",
}


def report_sar_drafting_node(state: InvestigationState) -> InvestigationState:
    t0 = time.time()
    cust = state.get("customer_data", {})
    alert = state.get("alert_data", {})
    risk = state.get("risk_evaluation", {})
    fact_sheet = state.get("fact_sheet", {"claims": [], "red_flags": []})
    decision = state.get("filing_decision", {"decision": "NO_FILE", "tier": None, "reasons": []})

    drafted = llm_service.draft_str_narrative(fact_sheet, alert, cust, decision)
    is_str = decision.get("decision") == "FILE_STR"

    report: Dict[str, Any] = {
        "report_type": "STR_DRAFT" if is_str else "NO_FILE_MEMO",
        "case_id": state.get("case_id"),
        "alert_id": state.get("alert_id"),
        "alert_type": alert.get("alert_type"),
        "subject_name": cust.get("full_name"),
        "subject_id": cust.get("customer_id"),
        "subject_accounts": fact_sheet.get("subject_accounts", []),
        "window_label": fact_sheet.get("window_label"),
        "risk_score": risk.get("final_risk_score"),
        "risk_band": risk.get("final_risk_band"),
        "filing_decision": decision,
        "grounds_of_suspicion": fact_sheet.get("red_flags", []) if is_str else [],
        "claims": drafted["claims"],
        "modus_operandi": drafted["modus_operandi"],
        "drafted_by": drafted.get("drafted_by", "deterministic"),
        "requires_human_signoff": True,
        "recommended_action": decision.get("recommended_action"),
    }
    report["formatted_markdown_report"] = render_report_markdown(report)

    state["sar_report"] = report
    state["agent_trail"].append({
        "agent_name": "ReportDraftingAgent",
        "action": "STR_DRAFTED" if is_str else "CLOSURE_MEMO_DRAFTED",
        "status": "COMPLETED",
        "duration_ms": round((time.time() - t0) * 1000, 2),
        "summary": (
            f"Drafted {'FIU-IND STR' if is_str else 'alert closure memo'} for {cust.get('full_name')} "
            f"with {len(report['claims'])} evidence-linked claims (drafted by {report['drafted_by']})."
        ),
        "details": {k: v for k, v in report.items() if k != "formatted_markdown_report"},
        "timestamp": datetime.datetime.utcnow().isoformat(),
    })
    return state


def _claim_line(c: Dict[str, Any]) -> str:
    mark = {"VERIFIED": "✓", "UNVERIFIED": "✗"}.get(c.get("status"), "?")
    line = f"- [{mark}] {c.get('text')}  _(evidence: {len(c.get('evidence_ids') or [])} record(s), {c.get('claim_id')})_"
    for note in c.get("verification_notes") or []:
        line += f"\n    - ⚠ {note}"
    return line


def render_report_markdown(r: Dict[str, Any]) -> str:
    d = r.get("filing_decision") or {}
    v = r.get("verification") or {}
    is_str = r.get("report_type") == "STR_DRAFT"
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    title = "SUSPICIOUS TRANSACTION REPORT (STR) — DRAFT FOR FIU-IND" if is_str else "ALERT CLOSURE MEMO — NO STR FILED"
    status = v.get("approval_status", "NOT YET FACT-CHECKED")
    out = [
        f"# {title}",
        f"**Approval status:** {status}  ",
        f"**Case:** {r.get('case_id')} · **Alert:** {r.get('alert_id')} ({r.get('alert_type')})  ",
        f"**Generated:** {now} · **Drafted by:** {r.get('drafted_by')}  ",
    ]
    if v:
        comp = v.get("completeness", {})
        out.append(
            f"**Fact check:** {v.get('verified_claims')}/{v.get('total_claims')} claims verified · "
            f"**Completeness (5W1H):** {comp.get('score', 0):.0%}"
            + (f" — missing: {', '.join(comp.get('missing', []))}" if comp.get("missing") else "")
        )
    out += [
        "",
        "## 1. Decision",
        f"- **Decision:** {d.get('decision')}" + (f" — {TIER_LABELS.get(d.get('tier'), d.get('tier'))}" if d.get("tier") else ""),
        f"- **Deterministic risk score:** {r.get('risk_score')} / 100 ({r.get('risk_band')})",
        f"- **Recommended action:** {d.get('recommended_action')}",
        "",
        "## 2. Subject (Who)",
        f"- **Name:** {r.get('subject_name')}",
        f"- **Customer ID:** {r.get('subject_id')}",
        f"- **Account(s):** {', '.join(r.get('subject_accounts') or [])}",
        "",
    ]
    if is_str:
        out.append("## 3. Grounds of Suspicion (Why)")
        for f in r.get("grounds_of_suspicion") or []:
            ref = f" (see {f['claim_id']})" if f.get("claim_id") else ""
            out.append(f"- **{f['code']}** [{f.get('strength')}]: {f['description']}{ref}")
    else:
        out.append("## 3. Reason for Not Filing")
        for reason in d.get("reasons") or []:
            out.append(f"- {reason}")
    out += [
        "",
        f"## 4. Evidence-Linked Facts (What / When / Where) — {r.get('window_label')}",
        "_Every line below was re-computed from the ledger by the Fact Checker. ✓ = verified, ✗ = not supported._",
    ]
    out += [_claim_line(c) for c in r.get("claims") or []]
    out += [
        "",
        "## 5. Modus Operandi (How)",
        r.get("modus_operandi") or "_Not provided._",
    ]
    for issue in v.get("free_text_issues") or []:
        out.append(f"> ⚠ {issue}")
    out += [
        "",
        "## 6. Sign-off",
        "> Draft prepared by SentinelGraph. Under PMLA, the decision to file and the content of any STR "
        "must be reviewed and authorised by the Principal Officer. "
        + ("Approval is blocked until every claim above is verified or corrected."
           if status == "BLOCKED_UNVERIFIED_CLAIMS" else ""),
    ]
    return "\n".join(out)
