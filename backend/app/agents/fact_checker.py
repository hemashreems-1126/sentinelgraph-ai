"""
Fact Checker Agent (deterministic, no LLM).

The LLM may write the words of the report, but it is never trusted with the facts.
For every claim this agent:
  1. looks up each evidence ID in the database (missing ID → unverified)
  2. recomputes every assertion from those rows only (wrong number → unverified)
  3. checks that every number written in the claim's text matches an assertion value
     (an invented number such as "+3.14 standard deviations" → unverified)
It also flags any numbers that appear in free-text sections, scores the report for
5W1H completeness (who / what / when / where / why / how), and blocks analyst approval
while any claim is unverified.
"""
import re
import time
import datetime
from typing import Any, Dict, List, Tuple

from app.agents.evidence_metrics import (
    ACCOUNT_METRICS, ALL_METRICS, CUSTOMER_METRICS, LEDGER_METRICS, compare, compute_account_metric,
    compute_customer_metric, compute_first_time_payers, compute_transaction_metric,
)
from app.agents.state import InvestigationState
from app.db.models import Account, Customer, Transaction
from app.db.session import SessionLocal

# A number that is not glued to letters/underscores (so IDs like TXN_000123 are ignored).
_NUMBER_RE = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?(?![\w])")


def extract_numbers(text: str) -> List[float]:
    out = []
    for m in _NUMBER_RE.findall(text or ""):
        try:
            out.append(float(m.replace(",", "")))
        except ValueError:
            pass
    return out


def _number_supported(n: float, assertions: List[Dict[str, Any]]) -> bool:
    for a in assertions:
        v = a.get("value")
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if abs(float(v) - n) <= max(1.0, abs(float(v)) * 0.0005):
                return True
    return False


def verify_claim(claim: Dict[str, Any], db) -> Dict[str, Any]:
    reasons: List[str] = []
    evidence_ids = claim.get("evidence_ids") or []
    assertions = claim.get("assertions") or []
    recomputed: Dict[str, Any] = {}

    if not evidence_ids:
        reasons.append("No evidence attached.")
    if not assertions:
        reasons.append("No checkable assertion attached.")

    txn_metrics = [a for a in assertions if a.get("metric") not in CUSTOMER_METRICS | ACCOUNT_METRICS]
    cust_metrics = [a for a in assertions if a.get("metric") in CUSTOMER_METRICS]
    acct_metrics = [a for a in assertions if a.get("metric") in ACCOUNT_METRICS]

    for a in assertions:
        if a.get("metric") not in ALL_METRICS:
            reasons.append(f"Unknown metric '{a.get('metric')}'.")

    # Every cited ID must exist somewhere in the ledger (transaction, account or customer).
    if evidence_ids:
        known = {t[0] for t in db.query(Transaction.txn_id).filter(Transaction.txn_id.in_(evidence_ids)).all()}
        known |= {a[0] for a in db.query(Account.account_id).filter(Account.account_id.in_(evidence_ids)).all()}
        known |= {c[0] for c in db.query(Customer.customer_id).filter(Customer.customer_id.in_(evidence_ids)).all()}
        unknown = [e for e in evidence_ids if e not in known]
        if unknown:
            reasons.append(f"{len(unknown)} cited record(s) do not exist: {', '.join(unknown[:3])}.")

    txns: List[Transaction] = []
    if txn_metrics and evidence_ids:
        txns = db.query(Transaction).filter(Transaction.txn_id.in_(evidence_ids)).all()
        missing = set(evidence_ids) - {t.txn_id for t in txns}
        if missing and not any(r.startswith(f"{len(missing)} cited record") for r in reasons):
            reasons.append(f"{len(missing)} evidence ID(s) are not transactions.")

    customer = None
    if cust_metrics and evidence_ids:
        customer = db.query(Customer).filter(Customer.customer_id == evidence_ids[0]).first()
        if customer is None:
            reasons.append("Customer record not found.")

    account = anchor_txn = None
    if acct_metrics:
        if len(evidence_ids) < 2:
            reasons.append("Account-age claims need [account_id, transaction_id] as evidence.")
        else:
            account = db.query(Account).filter(Account.account_id == evidence_ids[0]).first()
            anchor_txn = db.query(Transaction).filter(Transaction.txn_id == evidence_ids[1]).first()
            if account is None or anchor_txn is None:
                reasons.append("Account or anchoring transaction not found.")

    for a in assertions:
        metric, op, stated = a.get("metric"), a.get("op", "=="), a.get("value")
        if metric not in ALL_METRICS:
            continue
        try:
            if metric in LEDGER_METRICS:
                actual = compute_first_time_payers(db, txns, claim.get("subject_accounts"))
            elif metric in ACCOUNT_METRICS:
                actual = compute_account_metric(metric, account, anchor_txn, db)
            elif metric in CUSTOMER_METRICS:
                actual = compute_customer_metric(metric, customer)
            else:
                actual = compute_transaction_metric(metric, txns, claim.get("subject_accounts"))
        except Exception as e:  # defensive: a malformed claim must fail, not crash the pipeline
            reasons.append(f"Could not compute {metric}: {e}")
            continue
        recomputed[metric] = actual
        if not compare(metric, op, stated, actual):
            reasons.append(f"{metric}: report says {op} {stated}, ledger shows {actual}.")

    for n in extract_numbers(claim.get("text", "")):
        if not _number_supported(n, assertions):
            reasons.append(f"Number {n:g} in the text is not backed by any checked assertion.")

    return {
        **claim,
        "status": "VERIFIED" if not reasons else "UNVERIFIED",
        "verification_notes": reasons,
        "recomputed": recomputed,
    }


def assess_completeness(report: Dict[str, Any], claims: List[Dict[str, Any]]) -> Dict[str, Any]:
    verified = {c["category"] for c in claims if c["status"] == "VERIFIED"}
    is_str = report.get("report_type") == "STR_DRAFT"
    checks = {
        "who": bool(report.get("subject_name") and report.get("subject_id")),
        "what": "what" in verified,
        "when": "when" in verified,
        "where": "where" in verified,
        "why": bool(report.get("grounds_of_suspicion")) if is_str
               else bool((report.get("filing_decision") or {}).get("reasons")),
        "how": bool((report.get("modus_operandi") or "").strip()),
    }
    return {
        "checks": checks,
        "score": round(sum(checks.values()) / len(checks), 2),
        "missing": [k for k, ok in checks.items() if not ok],
    }


def fact_check_report(report: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    db = SessionLocal()
    try:
        checked = [verify_claim(c, db) for c in report.get("claims", [])]
    finally:
        db.close()

    free_text_issues = []
    for field in ("modus_operandi",):
        nums = extract_numbers(report.get(field, ""))
        if nums:
            free_text_issues.append(
                f"'{field}' contains unchecked numbers {', '.join(f'{n:g}' for n in nums)} — numbers belong in claims."
            )

    n_ok = sum(c["status"] == "VERIFIED" for c in checked)
    blocked = n_ok < len(checked) or bool(free_text_issues) or not checked
    verification = {
        "total_claims": len(checked),
        "verified_claims": n_ok,
        "unverified_claims": len(checked) - n_ok,
        "grounding_rate": round(n_ok / len(checked), 3) if checked else 0.0,
        "free_text_issues": free_text_issues,
        "completeness": assess_completeness(report, checked),
        "approval_status": "BLOCKED_UNVERIFIED_CLAIMS" if blocked else "READY_FOR_REVIEW",
    }
    return {**report, "claims": checked, "verification": verification}, verification


def fact_checker_node(state: InvestigationState) -> InvestigationState:
    from app.agents.report_drafter import render_report_markdown  # avoid import cycle

    t0 = time.time()
    report, verification = fact_check_report(state.get("sar_report", {}))
    report["formatted_markdown_report"] = render_report_markdown(report)
    state["sar_report"] = report

    state["agent_trail"].append({
        "agent_name": "FactCheckerAgent (Deterministic Python)",
        "action": "REPORT_FACT_CHECKED",
        "status": "COMPLETED",
        "duration_ms": round((time.time() - t0) * 1000, 2),
        "summary": (
            f"{verification['verified_claims']}/{verification['total_claims']} claims verified against the ledger; "
            f"completeness {verification['completeness']['score']:.0%}; status {verification['approval_status']}."
        ),
        "details": verification,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    })
    return state
