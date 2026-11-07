"""
Behaviour Analysis Agent — compares the suspicious window with the account's OWN history.

(The previous version returned fixed z-scores per alert type — e.g. every velocity alert got
3.82 — so the "behavioural" part of the risk score measured nothing. Everything below is now
computed from the ledger.)

  baseline = the subject's transactions in the 45 days before the suspicious window
  velocity_z  = (transactions per day in the window − baseline mean per day) / baseline std
  amount_z    = (mean amount in the window − baseline mean amount) / baseline std
  outbound_ratio = money out ÷ money in during the window (capped at 1)
  dormancy_activation_score = 1.0 for an account with no baseline activity, falling to 0
                              as baseline activity reaches 10 transactions
"""
import time
import datetime
from typing import Any, Dict, List

import numpy as np

from app.agents.state import InvestigationState
from app.agents.fact_sheet import subject_accounts_for, suspicious_window
from app.db.models import Transaction
from app.db.session import SessionLocal

BASELINE_DAYS = 45  # long enough to include last month's rent/salary cycle


def _z(value: float, mean: float, std: float) -> float:
    return float((value - mean) / std) if std > 0 else 0.0


def compute_behavior(window: List[Transaction], all_txns: List[Transaction], subject: set) -> Dict[str, Any]:
    if not window:
        return {
            "baseline_days": BASELINE_DAYS, "baseline_txn_count": 0, "window_txn_count": 0,
            "velocity_z_score": 0.0, "amount_z_score": 0.0, "outbound_ratio": 0.0,
            "dormancy_activation_score": 0.0, "is_statistical_outlier": False,
        }
    w_start = min(t.timestamp for t in window)
    w_end = max(t.timestamp for t in window)
    b_start = w_start - datetime.timedelta(days=BASELINE_DAYS)
    baseline = [t for t in all_txns if b_start <= t.timestamp < w_start]

    # Velocity: transactions per day
    w_days = max(1.0, (w_end - w_start).total_seconds() / 86400.0)
    w_rate = len(window) / w_days
    daily = np.zeros(BASELINE_DAYS)
    for t in baseline:
        idx = min(BASELINE_DAYS - 1, int((t.timestamp - b_start).total_seconds() // 86400))
        daily[idx] += 1
    base_rate_mean = float(daily.mean())
    base_rate_std = max(float(daily.std()), 0.5)
    velocity_z = _z(w_rate, base_rate_mean, base_rate_std)

    # Amount: mean ticket size
    w_amounts = [t.amount for t in window]
    b_amounts = [t.amount for t in baseline]
    if len(b_amounts) >= 3:
        amount_z = _z(float(np.mean(w_amounts)), float(np.mean(b_amounts)), max(float(np.std(b_amounts)), 1.0))
    else:
        amount_z = 0.0  # not enough history to say anything

    inflow = sum(t.amount for t in window if t.receiver_account_id in subject and t.sender_account_id not in subject)
    outflow = sum(t.amount for t in window if t.sender_account_id in subject and t.receiver_account_id not in subject)
    outbound_ratio = min(1.0, outflow / inflow) if inflow > 0 else 0.0
    dormancy = max(0.0, 1.0 - len(baseline) / 10.0)

    return {
        "baseline_days": BASELINE_DAYS,
        "baseline_txn_count": len(baseline),
        "baseline_mean_amount": round(float(np.mean(b_amounts)), 2) if b_amounts else 0.0,
        "window_txn_count": len(window),
        "window_mean_amount": round(float(np.mean(w_amounts)), 2),
        "velocity_z_score": round(velocity_z, 2),
        "amount_z_score": round(amount_z, 2),
        "outbound_ratio": round(outbound_ratio, 3),
        "dormancy_activation_score": round(dormancy, 2),
        # Spiky but regular businesses are not outliers: velocity / pass-through only count for a
        # previously quiet account; ticket size counts on its own.
        "is_statistical_outlier": amount_z > 3.0 or ((velocity_z > 3.0 or outbound_ratio > 0.9) and dormancy > 0.5),
    }


def behavior_analysis_node(state: InvestigationState) -> InvestigationState:
    t0 = time.time()
    alert = state.get("alert_data", {})
    db = SessionLocal()
    try:
        subject = subject_accounts_for(db, alert, state.get("evidence_data", {}))
        all_txns, window, _ = suspicious_window(db, subject, alert.get("features_json") or {})
        stats = compute_behavior(window, all_txns, set(subject))
    finally:
        db.close()

    state["behavior_data"] = stats
    state["agent_trail"].append({
        "agent_name": "BehaviorAnalysisAgent",
        "action": "BEHAVIOR_ANALYZED",
        "status": "COMPLETED",
        "duration_ms": round((time.time() - t0) * 1000, 2),
        "summary": (
            f"Compared {stats['window_txn_count']} window transactions with {stats['baseline_txn_count']} in the prior "
            f"{BASELINE_DAYS} days: velocity z={stats['velocity_z_score']:.2f}, amount z={stats['amount_z_score']:.2f}, "
            f"out/in={stats['outbound_ratio']*100:.0f}%, dormancy={stats['dormancy_activation_score']:.2f}."
        ),
        "details": stats,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    })
    return state
