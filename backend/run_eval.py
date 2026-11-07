"""
SentinelGraph evaluation CLI.

  # Synthetic India-first benchmark (default)
  python run_eval.py --cases 200

  # External dataset the system did not generate (IBM AML, Kaggle)
  python run_eval.py --ibm path/to/HI-Small_Trans.csv --max-rows 200000 --cases 200

Runs in its own database file (eval.db by default) so it never touches the app's data, writes
evaluation_results.json and prints a summary. Every number is produced by actually running
detection, the multi-agent investigation, the filing decision and the fact checker.
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, HERE)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ibm", help="Path to an IBM AML transactions CSV (e.g. HI-Small_Trans.csv)")
    ap.add_argument("--max-rows", type=int, default=200_000, help="Rows to load from the IBM CSV")
    ap.add_argument("--cases", type=int, default=150, help="Alerts to fully investigate")
    ap.add_argument("--customers", type=int, default=1000, help="Synthetic customers")
    ap.add_argument("--transactions", type=int, default=15400, help="Synthetic background transactions")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--db", default=os.path.join(HERE, "eval.db"), help="SQLite file used for the run")
    ap.add_argument("--out", default=os.path.join(HERE, "evaluation_results.json"))
    args = ap.parse_args()

    if not os.environ.get("DATABASE_URL"):
        if os.path.exists(args.db):
            os.remove(args.db)
        os.environ["DATABASE_URL"] = f"sqlite:///{args.db}"

    from app.db.session import SessionLocal, init_db
    from app.services.monitor import transaction_monitor
    from app.utils.evaluation_runner import evaluation_runner

    init_db()
    db = SessionLocal()
    t0 = time.time()
    try:
        if args.ibm:
            from app.services.external_data import load_ibm_aml_csv
            stats = load_ibm_aml_csv(db, args.ibm, max_rows=args.max_rows)
            dataset = f"ibm-aml:{os.path.basename(args.ibm)}[:{args.max_rows}]"
        else:
            from app.services.data_generator import SyntheticAMLDataGenerator
            stats = SyntheticAMLDataGenerator(seed=args.seed).generate_and_seed_database(
                db, num_customers=args.customers, num_transactions=args.transactions)
            dataset = "synthetic-india-v2"
        print(f"[*] Loaded {dataset}: {stats}")
        alerts = transaction_monitor.scan_and_generate_alerts(db)
        print(f"[*] Monitoring raised {len(alerts)} alerts in {time.time() - t0:.0f}s; investigating up to {args.cases}...")
        res = evaluation_runner.run_benchmark_evaluation(
            db, split_type="TEST", seed=args.seed, max_cases=args.cases, dataset_name=dataset)
    finally:
        db.close()

    res["load_stats"] = stats
    with open(args.out, "w") as fh:
        json.dump(res, fh, indent=2, default=str)

    d, f, c = res["detection"], res["filing"], res["fact_check"]
    cm = f["confusion"]
    print("\n" + "=" * 64)
    print(f"  SentinelGraph evaluation — {dataset} (held-out TEST alerts)")
    print("=" * 64)
    print(f"  Detection   alerts={d['alerts_evaluated']}  precision={d['alert_precision']:.1%}  "
          f"controlled-account coverage={d['controlled_account_coverage']:.1%}")
    print(f"  Filing      cases={f['cases_investigated']}  precision={f['precision']:.1%}  recall={f['recall']:.1%}  "
          f"F1={f['f1']:.3f}  accuracy={f['accuracy']:.1%}")
    print(f"              TP={cm['true_positives']} FP={cm['false_positives']} FN={cm['false_negatives']} TN={cm['true_negatives']}"
          f"  alert reduction={f['alert_reduction_rate']:.1%}  risk-score ROC-AUC={f['risk_score_roc_auc']:.3f}")
    if f["hard_negative_cases"]:
        print(f"              legitimate look-alikes filed: {f['hard_negative_false_file_rate']:.1%} of {f['hard_negative_cases']}")
    print(f"  Fact check  genuine reports verified={c['genuine_reports_ready']:.1%}  grounding={c['mean_grounding_rate']:.1%}  "
          f"5W1H={c['mean_completeness_5w1h']:.1%}")
    print(f"              corrupted reports caught={c['corruption_catch_rate']:.1%} of {c['corrupted_reports_tested']}  "
          f"{c['catch_rate_by_corruption']}")
    print("=" * 64)
    print(f"[+] {res['runtime_seconds']}s — results saved to {args.out}")


if __name__ == "__main__":
    main()
