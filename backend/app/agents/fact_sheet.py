"""
Fact sheet builder (deterministic, no LLM).

Pulls the subject's transactions for the suspicious window straight from the database and
turns them into:
  * `claims`    — evidence-linked statements (with assertions the fact checker can recompute)
  * `red_flags` — India-specific grounds of suspicion, each pointing to its evidence

The filing decision and the STR drafter both work from this fact sheet, so the only numbers
that ever enter a report are numbers computed here from real rows.
"""
import datetime
from typing import Any, Dict, List

from app.agents.evidence_metrics import compute_first_time_payers, compute_transaction_metric, make_assertion
from app.db.models import Account, Transaction
from app.db.session import SessionLocal

PAN_CASH_THRESHOLD = 50000.0
WINDOW = datetime.timedelta(hours=24)


def _fmt_inr(x: float) -> str:
    return f"₹{x:,.2f}"


def _anchor_txn_ids(features: Dict[str, Any]) -> List[str]:
    ids: List[str] = []
    ids += features.get("sample_txn_ids") or []
    for k in ("inbound_txn", "outbound_txn", "transaction_id"):
        if features.get(k):
            ids.append(features[k])
    return ids


def _max_distinct_senders_24h(inbound: List[Transaction]) -> int:
    inbound = sorted(inbound, key=lambda t: t.timestamp)
    best = 0
    for i, t in enumerate(inbound):
        senders = {x.sender_account_id for x in inbound[i:] if x.timestamp - t.timestamp <= WINDOW}
        best = max(best, len(senders))
    return best


def _max_txns_in_15min(txns: List[Transaction]) -> List[Transaction]:
    txns = sorted(txns, key=lambda t: t.timestamp)
    best: List[Transaction] = []
    for i, t in enumerate(txns):
        burst = [x for x in txns[i:] if (x.timestamp - t.timestamp).total_seconds() <= 900]
        if len(burst) > len(best):
            best = burst
    return best


def subject_accounts_for(db, alert: Dict[str, Any], evidence: Dict[str, Any]) -> List[str]:
    """The account(s) under investigation. For a single-transaction alert it is the sender."""
    if alert.get("entity_type") == "TRANSACTION":
        t = db.query(Transaction).filter(Transaction.txn_id == alert.get("entity_id")).first()
        return [t.sender_account_id] if t else []
    return list(evidence.get("target_account_ids") or [alert.get("entity_id")])


def suspicious_window(db, subject_accounts: List[str], features: Dict[str, Any]):
    """All of the subject's transactions, and the suspicious window: ±24h around the
    transactions that triggered the alert (or the full history if the alert names none)."""
    all_txns = db.query(Transaction).filter(
        (Transaction.sender_account_id.in_(subject_accounts))
        | (Transaction.receiver_account_id.in_(subject_accounts))
    ).order_by(Transaction.timestamp.asc()).all() if subject_accounts else []
    anchor_ids = set(_anchor_txn_ids(features))
    anchors = [t for t in all_txns if t.txn_id in anchor_ids]
    if not anchors:
        return all_txns, all_txns, False
    start = min(t.timestamp for t in anchors) - WINDOW
    end = max(t.timestamp for t in anchors) + WINDOW
    return all_txns, [t for t in all_txns if start <= t.timestamp <= end], True


def build_fact_sheet(state: Dict[str, Any]) -> Dict[str, Any]:
    alert = state.get("alert_data", {})
    cust = state.get("customer_data", {})
    features = alert.get("features_json") or {}
    evidence = state.get("evidence_data", {})

    db = SessionLocal()
    try:
        subject_accounts = subject_accounts_for(db, alert, evidence)
        all_txns, window_txns, anchored = suspicious_window(db, subject_accounts, features)
        window_label = ("the 24 hours around the alerting transactions" if anchored
                        else "the full monitoring period")
        subj_set = set(subject_accounts)
        onward_pair = None
        for out_t in [t for t in window_txns if t.sender_account_id in subj_set
                      and t.receiver_account_id not in subj_set][:20]:
            nxt = db.query(Transaction).filter(
                Transaction.sender_account_id == out_t.receiver_account_id,
                Transaction.receiver_account_id != out_t.receiver_account_id,
                Transaction.timestamp > out_t.timestamp,
                Transaction.timestamp <= out_t.timestamp + datetime.timedelta(hours=2),
                Transaction.amount >= out_t.amount * 0.85,
            ).order_by(Transaction.timestamp).first()
            if nxt:
                onward_pair = (out_t, nxt)
                break
        prior_count = None
        if subject_accounts and window_txns:
            start = window_txns[0].timestamp - datetime.timedelta(days=30)
            prior_count = db.query(Transaction).filter(
                ((Transaction.sender_account_id == subject_accounts[0]) | (Transaction.receiver_account_id == subject_accounts[0])),
                Transaction.timestamp >= start, Transaction.timestamp < window_txns[0].timestamp,
            ).count()
        inbound_w = sorted([t for t in window_txns if t.receiver_account_id in subj_set
                            and t.sender_account_id not in subj_set], key=lambda t: t.timestamp)
        best_day: List[Transaction] = []
        best_new = 0
        for i, t in enumerate(inbound_w):
            day = [x for x in inbound_w[i:] if x.timestamp - t.timestamp <= WINDOW]
            if len({x.sender_account_id for x in day}) <= best_new:
                continue
            n_new = compute_first_time_payers(db, day, subject_accounts)
            if n_new > best_new:
                best_new, best_day = n_new, day
        accounts = {a.account_id: a for a in db.query(Account).filter(Account.account_id.in_(subject_accounts)).all()}
        round_trip_ids = list((state.get("graph_data") or {}).get("round_trip_txn_ids") or [])
        round_trip_txns = (
            db.query(Transaction).filter(Transaction.txn_id.in_(round_trip_ids)).order_by(Transaction.timestamp).all()
            if round_trip_ids else []
        )
    finally:
        db.close()

    subj = set(subject_accounts)
    inbound = [t for t in window_txns if t.receiver_account_id in subj]
    outbound = [t for t in window_txns if t.sender_account_id in subj]
    upi_in = [t for t in inbound if t.txn_type == "UPI"]
    cash_sub_pan = [
        t for t in inbound
        if t.txn_type == "CASH_DEPOSIT" and 45000.0 <= t.amount < PAN_CASH_THRESHOLD
    ]
    ids = lambda xs: [t.txn_id for t in xs]

    claims: List[Dict[str, Any]] = []

    def add_claim(cid: str, category: str, text: str, evidence_ids: List[str], assertions: List[Dict]):
        claims.append({
            "claim_id": cid,
            "category": category,          # who / what / when / where / why
            "text": text,
            "evidence_ids": evidence_ids,
            "subject_accounts": subject_accounts,
            "assertions": assertions,
            "status": "UNCHECKED",
        })

    # WHO
    if cust.get("customer_id") and cust.get("occupation"):
        add_claim(
            "C_KYC", "who",
            f"The customer's declared occupation is {cust['occupation']}.",
            [cust["customer_id"]],
            [make_assertion("kyc_occupation", cust["occupation"])],
        )

    # WHO — account age at the start of the suspicious activity
    account_age_days = None
    if subject_accounts and window_txns and accounts.get(subject_accounts[0]):
        acc = accounts[subject_accounts[0]]
        first = window_txns[0]
        if acc.opened_at is not None and first.timestamp >= acc.opened_at:
            account_age_days = (first.timestamp - acc.opened_at).days
            add_claim(
                "C_ACCOUNT_AGE", "who",
                f"The subject account had been open for {account_age_days} days when this activity began.",
                [acc.account_id, first.txn_id],
                [make_assertion("account_age_days", account_age_days)],
            )

    subject_acc = accounts.get(subject_accounts[0]) if subject_accounts else None
    if subject_acc is not None and window_txns:
        add_claim(
            "C_ACCOUNT_TYPE", "who",
            f"The subject account is a {'business (current)' if subject_acc.account_type == 'BUSINESS' else 'personal'} account.",
            [subject_acc.account_id, window_txns[0].txn_id],
            [make_assertion("account_type", subject_acc.account_type)],
        )

    if prior_count is not None and accounts.get(subject_accounts[0]):
        add_claim(
            "C_PRIOR_ACTIVITY", "who",
            f"In the month before this activity the account made {prior_count} transactions.",
            [subject_accounts[0], window_txns[0].txn_id],
            [make_assertion("prior_txn_count_30d", prior_count)],
        )

    # WHAT — money in
    if inbound:
        total = compute_transaction_metric("total_amount", inbound)
        n = len(inbound)
        senders = compute_transaction_metric("distinct_senders", inbound)
        add_claim(
            "C_INFLOW", "what",
            f"The subject account received {_fmt_inr(total)} in {n} credits from {senders} distinct sender accounts.",
            ids(inbound),
            [make_assertion("total_amount", total), make_assertion("txn_count", n),
             make_assertion("distinct_senders", senders)],
        )

    # WHAT — money out
    if outbound:
        total = compute_transaction_metric("total_amount", outbound)
        n = len(outbound)
        recv = compute_transaction_metric("distinct_receivers", outbound)
        add_claim(
            "C_OUTFLOW", "what",
            f"The subject account sent {_fmt_inr(total)} in {n} debits to {recv} distinct beneficiary accounts.",
            ids(outbound),
            [make_assertion("total_amount", total), make_assertion("txn_count", n),
             make_assertion("distinct_receivers", recv)],
        )

    # WHEN
    if len(window_txns) >= 2:
        n = len(window_txns)
        mins = compute_transaction_metric("time_span_minutes", window_txns)
        if mins <= 1440:
            text = f"These {n} transactions took place within {int(mins)} minutes."
            a = make_assertion("time_span_minutes", mins)
        elif mins > 72 * 60:
            days = compute_transaction_metric("time_span_days", window_txns)
            text = f"These {n} transactions took place over {days} days."
            a = make_assertion("time_span_days", days)
        else:
            hrs = compute_transaction_metric("time_span_hours", window_txns)
            text = f"These {n} transactions took place over {hrs} hours."
            a = make_assertion("time_span_hours", hrs)
        add_claim("C_TIMING", "when", text, ids(window_txns), [make_assertion("txn_count", n), a])

    # WHERE — channels used
    if window_txns:
        types = compute_transaction_metric("txn_types", window_txns)
        add_claim(
            "C_CHANNELS", "where",
            f"Funds moved through these channels: {', '.join(types)}.",
            ids(window_txns),
            [make_assertion("txn_types", types)],
        )

    # WHY — pass-through
    pct = 0
    if inbound and outbound:
        flow = list({t.txn_id: t for t in inbound + outbound}.values())  # self-transfers counted once
        pct = compute_transaction_metric("outflow_inflow_pct", flow, subject_accounts)
        add_claim(
            "C_PASSTHROUGH", "why",
            f"Outgoing payments equalled {int(pct)}% of the money received in the same period.",
            ids(flow),
            [make_assertion("outflow_inflow_pct", pct)],
        )

    # WHY — first-time payers (strangers), the signature of scam victims paying a mule.
    # Regular customers of a shop or flatmates paying rent every month are NOT first-time payers.
    if best_new >= 2:
        add_claim(
            "C_NEW_PAYERS", "why",
            f"Within one day, {best_new} accounts that had never transacted with this account before paid into it.",
            ids(best_day),
            [make_assertion("first_time_payers", best_new)],
        )

    # WHY — UPI collection
    if len(upi_in) >= 2:
        n = len(upi_in)
        m = compute_transaction_metric("distinct_senders", upi_in)
        add_claim(
            "C_UPI", "why",
            f"{n} of the credits came via UPI from {m} distinct payer accounts.",
            ids(upi_in),
            [make_assertion("txn_count", n), make_assertion("distinct_senders", m)],
        )

    # WHY — cash just under the PAN threshold
    if cash_sub_pan:
        n = len(cash_sub_pan)
        total = compute_transaction_metric("total_amount", cash_sub_pan)
        add_claim(
            "C_CASH_PAN", "why",
            f"{n} credits were cash deposits, each below ₹50,000 (the PAN-quoting threshold), totaling {_fmt_inr(total)}.",
            ids(cash_sub_pan),
            [make_assertion("txn_count", n), make_assertion("max_amount", PAN_CASH_THRESHOLD, "<"),
             make_assertion("total_amount", total)],
        )

    # WHY — many payments to ONE beneficiary in minutes (split payments / drain attack).
    # Payroll is the opposite: many different beneficiaries, one payment each.
    split_burst: List[Transaction] = []
    by_receiver: Dict[str, List[Transaction]] = {}
    for t in outbound:
        by_receiver.setdefault(t.receiver_account_id, []).append(t)
    for r_txns in by_receiver.values():
        burst = _max_txns_in_15min(r_txns)
        if len(burst) > len(split_burst):
            split_burst = burst
    if len(split_burst) >= 5:
        n = len(split_burst)
        mins = compute_transaction_metric("time_span_minutes", split_burst)
        add_claim(
            "C_SPLIT_PAYMENTS", "why",
            f"{n} separate payments went to the same beneficiary account within {int(mins)} minutes.",
            ids(split_burst),
            [make_assertion("txn_count", n), make_assertion("distinct_receivers", 1),
             make_assertion("time_span_minutes", mins)],
        )

    # WHY — the beneficiary passed the money straight on (layering chain)
    if onward_pair:
        out_t, nxt = onward_pair
        pair = [out_t, nxt]
        pct_on = compute_transaction_metric("outflow_inflow_pct", pair, [out_t.receiver_account_id])
        mins_on = compute_transaction_metric("time_span_minutes", pair)
        claims.append({
            "claim_id": "C_ONWARD", "category": "why",
            "text": f"The receiving account passed on {int(pct_on)}% of that payment within {int(mins_on)} minutes.",
            "evidence_ids": ids(pair),
            "subject_accounts": [out_t.receiver_account_id],
            "assertions": [make_assertion("outflow_inflow_pct", pct_on), make_assertion("time_span_minutes", mins_on)],
            "status": "UNCHECKED",
        })

    # WHY — time-ordered round trip found by the Graph agent
    if round_trip_txns:
        n = len(round_trip_txns)
        hrs = compute_transaction_metric("time_span_hours", round_trip_txns)
        add_claim(
            "C_ROUNDTRIP", "why",
            f"Money left the subject account and returned to it through {n} transfers in {hrs} hours.",
            ids(round_trip_txns),
            [make_assertion("txn_count", n), make_assertion("time_span_hours", hrs)],
        )

    # ---------------- Red flags (grounds of suspicion) ----------------
    red_flags: List[Dict[str, Any]] = []
    inflow_total = sum(t.amount for t in inbound)
    # Pass-through only means something in a short window, and only if outflow ≈ inflow
    # (outflow far above inflow is just spending an existing balance).
    if anchored and inflow_total > 0 and 80 <= pct <= 110:
        red_flags.append({"code": "RAPID_PASS_THROUGH", "strength": "STRONG",
                          "description": "Most of the money received was moved out again in the same period.",
                          "claim_id": "C_PASSTHROUGH"})
    if best_new >= 5:
        red_flags.append({"code": "MANY_UNRELATED_PAYERS", "strength": "STRONG",
                          "description": "Five or more accounts with no previous relationship paid in within a single day.",
                          "claim_id": "C_NEW_PAYERS"})
    if len(cash_sub_pan) >= 3:
        red_flags.append({"code": "CASH_BELOW_PAN_THRESHOLD", "strength": "STRONG",
                          "description": "Repeated cash deposits kept just under the PAN-quoting threshold.",
                          "claim_id": "C_CASH_PAN"})
    if len(split_burst) >= 5:
        red_flags.append({"code": "SPLIT_PAYMENTS_SAME_BENEFICIARY", "strength": "STRONG",
                          "description": "Repeated payments to one beneficiary within minutes, splitting a larger amount.",
                          "claim_id": "C_SPLIT_PAYMENTS"})
    elif len(_max_txns_in_15min(window_txns)) >= 5:
        red_flags.append({"code": "HIGH_VELOCITY", "strength": "MODERATE",
                          "description": "Five or more transactions within fifteen minutes.",
                          "claim_id": "C_TIMING"})
    intel = state.get("intelligence_data", {})
    if intel.get("sanctions_match"):
        red_flags.append({"code": "SANCTIONS_MATCH", "strength": "STRONG",
                          "description": "Customer matches a sanctions list (mock feed).", "claim_id": None})
    elif intel.get("pep_match"):
        red_flags.append({"code": "PEP_MATCH", "strength": "MODERATE",
                          "description": "Customer is a politically exposed person (mock feed).", "claim_id": None})
    if round_trip_txns:
        red_flags.append({"code": "CIRCULAR_FLOW", "strength": "MODERATE",
                          "description": "Money left the account and came back to it in time order within three days.",
                          "claim_id": "C_ROUNDTRIP"})
    moving_money = any(f["code"] in ("RAPID_PASS_THROUGH", "MANY_UNRELATED_PAYERS") for f in red_flags)
    if onward_pair and any(f["code"] == "RAPID_PASS_THROUGH" for f in red_flags):
        red_flags.append({"code": "ONWARD_LAYERING", "strength": "MODERATE",
                          "description": "The next account in the chain also passed the money on within two hours.",
                          "claim_id": "C_ONWARD"})
    if subject_acc is not None and subject_acc.account_type != "BUSINESS" and any(
        f["code"] == "MANY_UNRELATED_PAYERS" for f in red_flags
    ):
        red_flags.append({"code": "PERSONAL_ACCOUNT_COLLECTION", "strength": "MODERATE",
                          "description": "A personal (non-business) account is collecting money from many unrelated payers.",
                          "claim_id": "C_ACCOUNT_TYPE"})
    behaviour = state.get("behavior_data") or {}
    if behaviour.get("is_statistical_outlier"):
        red_flags.append({"code": "BEHAVIOUR_OUTLIER", "strength": "MODERATE",
                          "description": "Activity is far outside this account's own pattern for the previous month "
                                         "(see Behaviour agent statistics).",
                          "claim_id": None})
    if prior_count is not None and prior_count <= 2 and moving_money:
        red_flags.append({"code": "DORMANT_ACCOUNT_ACTIVATED", "strength": "MODERATE",
                          "description": "An almost inactive account suddenly started moving money for others.",
                          "claim_id": "C_PRIOR_ACTIVITY"})
    if account_age_days is not None and account_age_days < 90 and (
        any(f["code"] in ("RAPID_PASS_THROUGH", "MANY_UNRELATED_PAYERS") for f in red_flags)
    ):
        red_flags.append({"code": "NEW_ACCOUNT_HIGH_ACTIVITY", "strength": "MODERATE",
                          "description": "A recently opened account is already moving money for many others.",
                          "claim_id": "C_ACCOUNT_AGE"})
    if (evidence.get("prior_alerts_on_file") or 0) >= 2:
        red_flags.append({"code": "REPEAT_ALERTS", "strength": "MODERATE",
                          "description": "The account already has two or more earlier alerts.", "claim_id": None})

    return {
        "subject_accounts": subject_accounts,
        "window_label": window_label,
        "window_txn_count": len(window_txns),
        "claims": claims,
        "red_flags": red_flags,
    }
