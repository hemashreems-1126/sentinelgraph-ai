"""
Staged, honest evaluation of SentinelGraph.

Every number here comes from actually running the system — nothing is sampled from the labels.
(The previous version generated random scores *conditioned on the ground-truth label*, which
made "100% recall / ROC-AUC 0.99" meaningless. That code has been removed.)

Ground truth (evaluation only, never visible to agents/rules/LLM):
  an alert is truly suspicious if its subject account is controlled by the synthetic criminal
  network (Account.fraud_role). Victims, smurf/feeder accounts and the legitimate look-alikes
  (merchants, payroll, rent splits, cash businesses) are negatives.

Stages
  1. Detection      — how noisy are the alerts the rules + Isolation Forest raise?
  2. Filing         — does the investigation pipeline file STRs for the right alerts and
                      close the rest? (precision / recall / F1 / ROC-AUC of the risk score,
                      alert reduction, false-file rate on hard negatives)
  3. Fact-checking  — grounding rate of genuine reports, and the catch rate when reports are
                      deliberately corrupted the way an LLM might corrupt them.
"""
import copy
import datetime
import random
import time
import uuid
from collections import Counter, defaultdict
from typing import Any, Dict, List

from sklearn.metrics import roc_auc_score
from sqlalchemy.orm import Session

from app.agents.fact_checker import fact_check_report
from app.db.models import Account, Alert, EvaluationMetricRecord, Transaction
from app.services.data_generator import SyntheticAMLDataGenerator
from app.services.monitor import transaction_monitor


def _ratio(a: float, b: float) -> float:
    return round(a / b, 4) if b else 0.0


def _prf(tp: int, fp: int, fn: int, tn: int) -> Dict[str, float]:
    p = _ratio(tp, tp + fp)
    r = _ratio(tp, tp + fn)
    return {
        "precision": p,
        "recall": r,
        "f1": round(2 * p * r / (p + r), 4) if (p + r) else 0.0,
        "accuracy": _ratio(tp + tn, tp + fp + fn + tn),
    }


# ---------------- report corruption (stage 3) ----------------

def _corruptions(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Five ways an LLM can get a report wrong. Each returns a corrupted copy."""
    out = []
    claims = report.get("claims") or []
    numeric = [c for c in claims if any(isinstance(a.get("value"), (int, float)) and not isinstance(a.get("value"), bool)
                                       for a in c.get("assertions", []))]
    if numeric:
        # 1. changes a number in the sentence only
        r = copy.deepcopy(report); c = next(x for x in r["claims"] if x["claim_id"] == numeric[0]["claim_id"])
        c["text"] = c["text"] + " This involved 37 additional transfers."
        out.append({"kind": "number_added_to_text", "report": r})
        # 2. inflates a stated value (sentence and assertion changed together)
        r = copy.deepcopy(report); c = next(x for x in r["claims"] if x["claim_id"] == numeric[0]["claim_id"])
        a = next(a for a in c["assertions"] if isinstance(a.get("value"), (int, float)) and not isinstance(a.get("value"), bool))
        a["value"] = round(float(a["value"]) * 1.5 + 3, 2)
        out.append({"kind": "inflated_value", "report": r})
    if claims:
        # 3. cites a transaction that does not exist
        r = copy.deepcopy(report)
        r["claims"][0]["evidence_ids"] = list(r["claims"][0]["evidence_ids"]) + ["TXN_FABRICATED_000"]
        out.append({"kind": "fabricated_evidence_id", "report": r})
    # 4. adds a claim with no evidence (like the old '+3.14 standard deviations' template)
    r = copy.deepcopy(report)
    r.setdefault("claims", []).append({
        "claim_id": "C_INJECTED", "category": "why", "text": "Velocity deviated 3.14 standard deviations from baseline.",
        "evidence_ids": [], "assertions": [], "subject_accounts": [],
    })
    out.append({"kind": "unsupported_claim", "report": r})
    # 5. puts a number in free text
    r = copy.deepcopy(report)
    r["modus_operandi"] = (r.get("modus_operandi") or "") + " Around 40 victims were affected."
    out.append({"kind": "number_in_free_text", "report": r})
    return out


class EvaluationRunner:

    def run_benchmark_evaluation(
        self,
        db: Session,
        split_type: str = "TEST",
        seed: int = 42,
        max_cases: int = 120,
        dataset_name: str = "synthetic-india-v2",
    ) -> Dict[str, Any]:
        from app.agents.workflow import execute_investigation_case  # avoid import cycle at module load

        t_start = time.time()
        if db.query(Transaction).count() == 0:
            SyntheticAMLDataGenerator(seed=seed).generate_and_seed_database(db, num_customers=250, num_transactions=2000)
            transaction_monitor.scan_and_generate_alerts(db)

        controlled = {a.account_id: a.fraud_role for a in db.query(Account).filter(Account.fraud_role.isnot(None)).all()}
        lookalike_accounts = {
            t.receiver_account_id if t.fraud_pattern_type != "BENIGN_PAYROLL" else t.sender_account_id
            for t in db.query(Transaction).filter(Transaction.fraud_pattern_type.like("BENIGN_%")).all()
        }
        txn_sender = {}

        def subject_of(alert: Alert) -> str:
            if alert.entity_type == "TRANSACTION":
                if alert.entity_id not in txn_sender:
                    t = db.query(Transaction).filter(Transaction.txn_id == alert.entity_id).first()
                    txn_sender[alert.entity_id] = t.sender_account_id if t else ""
                return txn_sender[alert.entity_id]
            return alert.entity_id

        all_alerts = db.query(Alert).all()
        alerts = [a for a in all_alerts if a.split_type == split_type] or all_alerts

        # ---------------- Stage 1: detection ----------------
        per_type = defaultdict(lambda: {"alerts": 0, "true_suspicious": 0})
        for a in alerts:
            per_type[a.alert_type]["alerts"] += 1
            per_type[a.alert_type]["true_suspicious"] += int(subject_of(a) in controlled)
        alerted_accounts = {subject_of(a) for a in all_alerts}
        detection = {
            "alerts_evaluated": len(alerts),
            "alert_precision": _ratio(sum(v["true_suspicious"] for v in per_type.values()), len(alerts)),
            "controlled_accounts": len(controlled),
            "controlled_account_coverage": _ratio(len(alerted_accounts & set(controlled)), len(controlled)),
            "by_alert_type": {
                k: {**v, "precision": _ratio(v["true_suspicious"], v["alerts"])} for k, v in sorted(per_type.items())
            },
        }

        # ---------------- Stage 2: investigation + filing decision ----------------
        rng = random.Random(seed)
        by_type: Dict[str, List[Alert]] = defaultdict(list)
        for a in alerts:
            by_type[a.alert_type].append(a)
        per_type_quota = max(1, max_cases // max(1, len(by_type)))
        sample: List[Alert] = []
        for typ in sorted(by_type):
            xs = by_type[typ][:]
            rng.shuffle(xs)
            sample += xs[:per_type_quota]
        # Always include the hard negatives that were alerted — they are the real test.
        sample_ids = {a.alert_id for a in sample}
        sample += [a for a in alerts if subject_of(a) in lookalike_accounts and a.alert_id not in sample_ids][:30]
        alert_meta = [(a.alert_id, a.alert_type, subject_of(a)) for a in sample]

        rows = []
        reports = []
        for alert_id, alert_type, subject in alert_meta:
            t0 = time.time()
            state = execute_investigation_case(f"EVAL_{uuid.uuid4().hex[:8]}", alert_id, "static", persist=False)
            rep = state.get("sar_report", {})
            rows.append({
                "alert_type": alert_type,
                "y_true": int(subject in controlled),
                "lookalike": subject in lookalike_accounts and subject not in controlled,
                "filed": int(state.get("filing_decision", {}).get("decision") == "FILE_STR"),
                "tier": state.get("filing_decision", {}).get("tier"),
                "risk_score": float(state.get("risk_evaluation", {}).get("final_risk_score", 0.0)),
                "grounding": rep.get("verification", {}).get("grounding_rate", 0.0),
                "ready": rep.get("verification", {}).get("approval_status") == "READY_FOR_REVIEW",
                "completeness": rep.get("verification", {}).get("completeness", {}).get("score", 0.0),
                "seconds": time.time() - t0,
            })
            reports.append(rep)

        tp = sum(r["y_true"] and r["filed"] for r in rows)
        fp = sum((not r["y_true"]) and r["filed"] for r in rows)
        fn = sum(r["y_true"] and not r["filed"] for r in rows)
        tn = sum((not r["y_true"]) and not r["filed"] for r in rows)
        try:
            auc = float(roc_auc_score([r["y_true"] for r in rows], [r["risk_score"] for r in rows]))
        except ValueError:
            auc = 0.0
        lookalikes = [r for r in rows if r["lookalike"]]
        filing_by_type = defaultdict(lambda: Counter())
        for r in rows:
            filing_by_type[r["alert_type"]]["cases"] += 1
            filing_by_type[r["alert_type"]]["filed"] += r["filed"]
            filing_by_type[r["alert_type"]]["true_suspicious"] += r["y_true"]
            filing_by_type[r["alert_type"]]["correct"] += int(r["filed"] == r["y_true"])
        filing = {
            "cases_investigated": len(rows),
            "confusion": {"true_positives": tp, "false_positives": fp, "false_negatives": fn, "true_negatives": tn},
            **_prf(tp, fp, fn, tn),
            "risk_score_roc_auc": round(auc, 4),
            "alert_reduction_rate": _ratio(sum(not r["filed"] for r in rows), len(rows)),
            "hard_negative_cases": len(lookalikes),
            "hard_negative_false_file_rate": _ratio(sum(r["filed"] for r in lookalikes), len(lookalikes)),
            "tier_distribution": dict(Counter(r["tier"] for r in rows if r["filed"])),
            "avg_seconds_per_case": round(sum(r["seconds"] for r in rows) / len(rows), 3) if rows else 0.0,
            "by_alert_type": {k: dict(v) for k, v in sorted(filing_by_type.items())},
        }

        # ---------------- Stage 3: fact-check robustness ----------------
        caught = Counter(); total = Counter()
        for rep in reports:
            for corr in _corruptions(rep):
                _, v = fact_check_report(corr["report"])
                total[corr["kind"]] += 1
                caught[corr["kind"]] += int(v["approval_status"] == "BLOCKED_UNVERIFIED_CLAIMS")
        fact_check = {
            "genuine_reports": len(reports),
            "mean_grounding_rate": round(sum(r["grounding"] for r in rows) / len(rows), 4) if rows else 0.0,
            "genuine_reports_ready": _ratio(sum(r["ready"] for r in rows), len(rows)),
            "mean_completeness_5w1h": round(sum(r["completeness"] for r in rows) / len(rows), 4) if rows else 0.0,
            "corrupted_reports_tested": sum(total.values()),
            "corruption_catch_rate": _ratio(sum(caught.values()), sum(total.values())),
            "catch_rate_by_corruption": {k: _ratio(caught[k], total[k]) for k in sorted(total)},
        }

        metrics = {
            "dataset": dataset_name,
            "split": split_type,
            "seed": seed,
            "runtime_seconds": round(time.time() - t_start, 1),
            "ground_truth": "Alert subject account is controlled by the synthetic criminal network "
                            "(victims, feeders and legitimate look-alikes are negatives).",
            "detection": detection,
            "filing": filing,
            "fact_check": fact_check,
        }

        run_id = f"EVAL_{uuid.uuid4().hex[:8].upper()}"
        record = EvaluationMetricRecord(
            run_id=run_id,
            timestamp=datetime.datetime.utcnow(),
            split_type=split_type,
            total_samples=len(rows),
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            precision_score=filing["precision"],
            recall_score=filing["recall"],
            f1_score=filing["f1"],
            accuracy_score=filing["accuracy"],
            roc_auc=filing["risk_score_roc_auc"],
            confusion_matrix_json=filing["confusion"],
            classification_report_json={"filing_by_alert_type": filing["by_alert_type"]},
            metrics_json=metrics,
            dataset_name=dataset_name,
        )
        db.add(record)
        db.commit()
        return {"run_id": run_id, **metrics}


evaluation_runner = EvaluationRunner()
