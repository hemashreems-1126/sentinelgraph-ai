"""
Evidence metrics — the small, fixed vocabulary of facts a report claim is allowed to state.

Every claim in an STR draft carries `evidence_ids` (transaction IDs or a customer ID) and a
list of `assertions` such as {"metric": "total_amount", "op": "==", "value": 420000.0}.
The fact checker recomputes each metric from the database using ONLY those evidence IDs,
so a number the LLM invents (or copies wrongly) cannot pass verification.
"""
import datetime
from typing import Any, Dict, List, Optional, Sequence

from app.db.models import Account, Customer, Transaction

# Tolerances used when comparing a stated value with the recomputed value.
TOLERANCE = {
    "total_amount": 1.0,          # ₹1 (rounding)
    "max_amount": 1.0,
    "min_amount": 1.0,
    "txn_count": 0,
    "distinct_senders": 0,
    "distinct_receivers": 0,
    "time_span_minutes": 1.0,
    "time_span_hours": 0.1,
    "time_span_days": 0.1,
    "outflow_inflow_pct": 1.0,    # percentage points
    "account_age_days": 1.0,
    "first_time_payers": 0,
    "prior_txn_count_30d": 0,
}

CUSTOMER_METRICS = {"kyc_occupation"}
# evidence_ids = [account_id, first_activity_txn_id]
ACCOUNT_METRICS = {"account_age_days", "prior_txn_count_30d", "account_type"}
# metrics that need extra ledger lookups beyond the cited rows
LEDGER_METRICS = {"first_time_payers"}
TRANSACTION_METRICS = (set(TOLERANCE.keys()) | {"txn_types"}) - ACCOUNT_METRICS - LEDGER_METRICS
ALL_METRICS = TRANSACTION_METRICS | CUSTOMER_METRICS | ACCOUNT_METRICS | LEDGER_METRICS


def compute_first_time_payers(db, txns: Sequence[Transaction], subject_accounts: List[str]) -> int:
    """Distinct payers (into the subject) with no earlier transaction of any kind with the subject."""
    subj = set(subject_accounts or [])
    first_seen: Dict[str, Any] = {}
    for t in txns:
        if t.receiver_account_id in subj and t.sender_account_id not in subj:
            if t.sender_account_id not in first_seen or t.timestamp < first_seen[t.sender_account_id]:
                first_seen[t.sender_account_id] = t.timestamp
    count = 0
    for payer, ts in first_seen.items():
        earlier = db.query(Transaction.id).filter(
            (((Transaction.sender_account_id == payer) & (Transaction.receiver_account_id.in_(subj)))
             | ((Transaction.receiver_account_id == payer) & (Transaction.sender_account_id.in_(subj)))),
            Transaction.timestamp < ts,
        ).first()
        count += earlier is None
    return count


def compute_transaction_metric(
    metric: str,
    txns: Sequence[Transaction],
    subject_accounts: Optional[List[str]] = None,
) -> Any:
    """Recompute a metric over a list of Transaction rows."""
    if metric == "total_amount":
        return round(sum(t.amount for t in txns), 2)
    if metric == "max_amount":
        return round(max((t.amount for t in txns), default=0.0), 2)
    if metric == "min_amount":
        return round(min((t.amount for t in txns), default=0.0), 2)
    if metric == "txn_count":
        return len(txns)
    if metric == "distinct_senders":
        return len({t.sender_account_id for t in txns})
    if metric == "distinct_receivers":
        return len({t.receiver_account_id for t in txns})
    if metric in ("time_span_minutes", "time_span_hours", "time_span_days"):
        if len(txns) < 2:
            return 0.0
        ts = sorted(t.timestamp for t in txns)
        secs = (ts[-1] - ts[0]).total_seconds()
        if metric == "time_span_minutes":
            return round(secs / 60.0)
        if metric == "time_span_hours":
            return round(secs / 3600.0, 1)
        return round(secs / 86400.0, 1)
    if metric == "txn_types":
        return sorted({t.txn_type for t in txns})
    if metric == "outflow_inflow_pct":
        subj = set(subject_accounts or [])
        inflow = sum(t.amount for t in txns if t.receiver_account_id in subj)
        outflow = sum(t.amount for t in txns if t.sender_account_id in subj)
        return round(100.0 * outflow / inflow) if inflow > 0 else 0
    raise ValueError(f"Unknown transaction metric: {metric}")


def compute_customer_metric(metric: str, customer: Optional[Customer]) -> Any:
    if customer is None:
        return None
    if metric == "kyc_occupation":
        return customer.occupation
    raise ValueError(f"Unknown customer metric: {metric}")


def compute_account_metric(metric: str, account: Optional[Account], txn: Optional[Transaction], db=None) -> Any:
    if account is None or txn is None:
        return None
    if metric == "account_age_days":
        return (txn.timestamp - account.opened_at).days if account.opened_at else None
    if metric == "account_type":
        return account.account_type
    if metric == "prior_txn_count_30d":
        start = txn.timestamp - datetime.timedelta(days=30)
        return db.query(Transaction).filter(
            ((Transaction.sender_account_id == account.account_id) | (Transaction.receiver_account_id == account.account_id)),
            Transaction.timestamp >= start, Transaction.timestamp < txn.timestamp,
        ).count()
    raise ValueError(f"Unknown account metric: {metric}")


def compare(metric: str, op: str, stated: Any, actual: Any) -> bool:
    """Compare a stated value with the recomputed value using the metric's tolerance."""
    if actual is None:
        return False
    if isinstance(stated, list) or isinstance(actual, list):
        return op == "==" and sorted(map(str, stated or [])) == sorted(map(str, actual or []))
    if isinstance(stated, str) or isinstance(actual, str):
        return op == "==" and str(stated).strip().lower() == str(actual).strip().lower()
    tol = TOLERANCE.get(metric, 0)
    try:
        s, a = float(stated), float(actual)
    except (TypeError, ValueError):
        return False
    if op == "==":
        return abs(s - a) <= tol
    if op == "<":
        return a < s
    if op == "<=":
        return a <= s + tol
    if op == ">":
        return a > s
    if op == ">=":
        return a >= s - tol
    return False


def make_assertion(metric: str, value: Any, op: str = "==") -> Dict[str, Any]:
    return {"metric": metric, "op": op, "value": value}
