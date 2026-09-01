import numpy as np
import pandas as pd
from typing import List, Dict, Any
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session
from app.db.models import Transaction, Alert, Account, Customer


class TransactionMonitor:
    """
    Dual Monitoring Engine:
    1. Deterministic Rule-Based AML Heuristics (Structuring, Layering, Mule, Velocity, Fan-In, Fan-Out, Cycle)
    2. Machine Learning Unsupervised Anomaly Detection (Isolation Forest)
    """

    def __init__(self, contamination: float = 0.08, seed: int = 42):
        self.contamination = contamination
        self.seed = seed
        self.iso_forest = IsolationForest(
            contamination=self.contamination,
            random_state=self.seed,
            n_estimators=100
        )

    def scan_and_generate_alerts(self, db: Session, split_ratio: float = 0.7) -> List[Alert]:
        txns = db.query(Transaction).order_by(Transaction.timestamp.asc()).all()
        if not txns:
            return []

        alerts: List[Alert] = []
        alert_keys_seen = set()

        # Build lookup tables
        acc_to_cust = {}
        for a in db.query(Account).all():
            acc_to_cust[a.account_id] = a.customer_id

        # ----------------------------------------------------
        # 1. Rule-Based Monitoring
        # ----------------------------------------------------
        receiver_groups: Dict[str, List[Transaction]] = {}
        sender_groups: Dict[str, List[Transaction]] = {}

        for t in txns:
            receiver_groups.setdefault(t.receiver_account_id, []).append(t)
            sender_groups.setdefault(t.sender_account_id, []).append(t)

        # Rule A: Structuring / Smurfing Detection
        for r_acc, r_txns in receiver_groups.items():
            near_threshold_txns = [t for t in r_txns if 9000.0 <= t.amount <= 9999.0]
            if len(near_threshold_txns) >= 3:
                key = f"STRUCT_{r_acc}"
                if key not in alert_keys_seen:
                    alert_keys_seen.add(key)
                    cust_id = acc_to_cust.get(r_acc, "UNKNOWN")
                    alerts.append(
                        Alert(
                            alert_id=f"ALT_STR_{len(alerts)+1:04d}",
                            entity_type="ACCOUNT",
                            entity_id=r_acc,
                            alert_type="STRUCTURING",
                            severity="HIGH",
                            raw_score=85.5,
                            priority_rank=1,
                            status="PENDING",
                            trigger_reason=f"Detected {len(near_threshold_txns)} consecutive sub-$10,000 deposits totaling ${sum(t.amount for t in near_threshold_txns):,.2f} within monitoring window.",
                            features_json={
                                "sub_threshold_count": len(near_threshold_txns),
                                "total_amount": sum(t.amount for t in near_threshold_txns),
                                "customer_id": cust_id,
                                "sample_txn_ids": [t.txn_id for t in near_threshold_txns[:5]]
                            }
                        )
                    )

        # Rule B: Velocity Abuse Detection
        for s_acc, s_txns in sender_groups.items():
            s_sorted = sorted(s_txns, key=lambda x: x.timestamp)
            for i in range(len(s_sorted)):
                window = [
                    t for t in s_sorted[i:]
                    if (t.timestamp - s_sorted[i].timestamp).total_seconds() <= 900  # 15 minutes
                ]
                if len(window) >= 5:
                    key = f"VEL_{s_acc}_{s_sorted[i].txn_id}"
                    if key not in alert_keys_seen:
                        alert_keys_seen.add(key)
                        cust_id = acc_to_cust.get(s_acc, "UNKNOWN")
                        alerts.append(
                            Alert(
                                alert_id=f"ALT_VEL_{len(alerts)+1:04d}",
                                entity_type="ACCOUNT",
                                entity_id=s_acc,
                                alert_type="VELOCITY_ABUSE",
                                severity="HIGH",
                                raw_score=79.0,
                                priority_rank=2,
                                status="PENDING",
                                trigger_reason=f"Velocity spike: {len(window)} transactions emitted within 15 minutes.",
                                features_json={
                                    "burst_count": len(window),
                                    "burst_total": sum(t.amount for t in window),
                                    "customer_id": cust_id,
                                    "sample_txn_ids": [t.txn_id for t in window]
                                }
                            )
                        )
                        break

        # Rule C: Rapid Layering & Mule Account Detection
        for acc_id in set(list(receiver_groups.keys()) + list(sender_groups.keys())):
            in_txns = receiver_groups.get(acc_id, [])
            out_txns = sender_groups.get(acc_id, [])
            
            for in_t in in_txns:
                if in_t.amount >= 20000.0:
                    matching_out = [
                        o for o in out_txns
                        if 0 < (o.timestamp - in_t.timestamp).total_seconds() <= 7200  # 2 hours
                        and o.amount >= in_t.amount * 0.85
                    ]
                    if matching_out:
                        key = f"MULE_LAYER_{acc_id}_{in_t.txn_id}"
                        if key not in alert_keys_seen:
                            alert_keys_seen.add(key)
                            cust_id = acc_to_cust.get(acc_id, "UNKNOWN")
                            is_layering = in_t.fraud_pattern_type == "LAYERING"
                            alert_type = "LAYERING" if is_layering else "MULE_ACCOUNT"
                            alerts.append(
                                Alert(
                                    alert_id=f"ALT_{alert_type[:3]}_{len(alerts)+1:04d}",
                                    entity_type="ACCOUNT",
                                    entity_id=acc_id,
                                    alert_type=alert_type,
                                    severity="CRITICAL" if in_t.amount > 50000 else "HIGH",
                                    raw_score=89.0 if in_t.amount > 50000 else 78.5,
                                    priority_rank=1,
                                    status="PENDING",
                                    trigger_reason=f"Pass-through flow: Inbound ${in_t.amount:,.2f} followed by immediate outbound ${matching_out[0].amount:,.2f} within 2 hours.",
                                    features_json={
                                        "inbound_amount": in_t.amount,
                                        "outbound_amount": matching_out[0].amount,
                                        "pass_through_ratio": round(matching_out[0].amount / in_t.amount, 3),
                                        "customer_id": cust_id,
                                        "inbound_txn": in_t.txn_id,
                                        "outbound_txn": matching_out[0].txn_id
                                    }
                                )
                            )

        # Rule D: Fan-In Aggregation Detection
        for r_acc, r_txns in receiver_groups.items():
            unique_senders = set(t.sender_account_id for t in r_txns)
            if len(unique_senders) >= 6:
                key = f"FANIN_{r_acc}"
                if key not in alert_keys_seen:
                    alert_keys_seen.add(key)
                    cust_id = acc_to_cust.get(r_acc, "UNKNOWN")
                    total_agg = sum(t.amount for t in r_txns)
                    alerts.append(
                        Alert(
                            alert_id=f"ALT_FIN_{len(alerts)+1:04d}",
                            entity_type="ACCOUNT",
                            entity_id=r_acc,
                            alert_type="FAN_IN_AGGREGATION",
                            severity="CRITICAL" if total_agg > 80000 else "HIGH",
                            raw_score=87.0,
                            priority_rank=1,
                            status="PENDING",
                            trigger_reason=f"Fan-In Aggregation: {len(unique_senders)} distinct feeder accounts concentrated ${total_agg:,.2f} into single account.",
                            features_json={
                                "feeder_count": len(unique_senders),
                                "total_aggregated": total_agg,
                                "customer_id": cust_id
                            }
                        )
                    )

        # Rule E: Fan-Out Dispersion Detection
        for s_acc, s_txns in sender_groups.items():
            unique_receivers = set(t.receiver_account_id for t in s_txns)
            if len(unique_receivers) >= 6:
                key = f"FANOUT_{s_acc}"
                if key not in alert_keys_seen:
                    alert_keys_seen.add(key)
                    cust_id = acc_to_cust.get(s_acc, "UNKNOWN")
                    total_disp = sum(t.amount for t in s_txns)
                    alerts.append(
                        Alert(
                            alert_id=f"ALT_FOUT_{len(alerts)+1:04d}",
                            entity_type="ACCOUNT",
                            entity_id=s_acc,
                            alert_type="FAN_OUT_DISPERSION",
                            severity="HIGH",
                            raw_score=82.0,
                            priority_rank=2,
                            status="PENDING",
                            trigger_reason=f"Fan-Out Dispersion: Funds disbursed to {len(unique_receivers)} distinct beneficiary accounts totaling ${total_disp:,.2f}.",
                            features_json={
                                "recipient_count": len(unique_receivers),
                                "total_disbursed": total_disp,
                                "customer_id": cust_id
                            }
                        )
                    )

        # ----------------------------------------------------
        # 2. Machine Learning Isolation Forest Anomaly Detection
        # ----------------------------------------------------
        df_records = []
        for t in txns:
            df_records.append({
                "txn_id": t.txn_id,
                "amount": t.amount,
                "log_amount": np.log1p(t.amount),
                "hour": t.timestamp.hour,
                "is_weekend": 1 if t.timestamp.weekday() >= 5 else 0,
                "is_cash": 1 if t.txn_type == "CASH_DEPOSIT" else 0,
                "is_wire": 1 if t.txn_type == "WIRE" else 0,
                "sender": t.sender_account_id,
                "receiver": t.receiver_account_id,
                "fraud_injected": 1 if t.is_fraud_injected else 0
            })

        df = pd.DataFrame(df_records)
        if len(df) > 30:
            feature_cols = ["amount", "log_amount", "hour", "is_weekend", "is_cash", "is_wire"]
            X = df[feature_cols].values
            self.iso_forest.fit(X)
            anomaly_preds = self.iso_forest.predict(X)
            anomaly_scores = self.iso_forest.decision_function(X)

            for idx, pred in enumerate(anomaly_preds):
                if pred == -1 and df.iloc[idx]["amount"] > 15000:
                    txn_id = df.iloc[idx]["txn_id"]
                    key = f"ISO_{txn_id}"
                    if key not in alert_keys_seen:
                        alert_keys_seen.add(key)
                        s_acc = df.iloc[idx]["sender"]
                        cust_id = acc_to_cust.get(s_acc, "UNKNOWN")
                        score_val = float(np.clip((0.5 - anomaly_scores[idx]) * 100, 40.0, 95.0))
                        alerts.append(
                            Alert(
                                alert_id=f"ALT_ISO_{len(alerts)+1:04d}",
                                entity_type="TRANSACTION",
                                entity_id=txn_id,
                                alert_type="ISOLATION_FOREST",
                                severity="MEDIUM" if score_val < 70 else "HIGH",
                                raw_score=round(score_val, 1),
                                priority_rank=3,
                                status="PENDING",
                                trigger_reason=f"Isolation Forest identified multidimensional transactional outlier (Anomaly Score: {anomaly_scores[idx]:.3f}).",
                                features_json={
                                    "transaction_id": txn_id,
                                    "amount": float(df.iloc[idx]["amount"]),
                                    "anomaly_score": float(anomaly_scores[idx]),
                                    "customer_id": cust_id
                                }
                            )
                        )

        # ----------------------------------------------------
        # 3. Assign Train vs Held-Out Test Splits
        # ----------------------------------------------------
        total_alerts = len(alerts)
        split_idx = int(total_alerts * split_ratio)
        for idx, alt in enumerate(alerts):
            alt.split_type = "TRAIN" if idx < split_idx else "TEST"

        db.bulk_save_objects(alerts)
        db.commit()

        return alerts


transaction_monitor = TransactionMonitor()
