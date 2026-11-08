import logging
import uuid
from sqlalchemy import select, func
from app.db.session import get_db_context
from app.db.models import Alert
from app.services.data_generator import SyntheticAMLDataGenerator
from app.services.monitor import transaction_monitor
from app.services.triage import alert_triage_service
from app.agents.workflow import execute_investigation_case
from app.utils.evaluation_runner import evaluation_runner

logger = logging.getLogger("SentinelGraph.Seed")


import threading

# Readiness flag: API data routes answer 503 ("warming up") until the demo data exists, so the
# web app shows "Waking up the server…" instead of an empty dashboard.
seed_state = {"ready": True, "stage": "ready"}


def start_background_seed():
    """Seed in a background thread so the server opens its port immediately (hosting platforms
    treat a server that doesn't listen within a few minutes as failed)."""
    seed_state.update(ready=False, stage="starting")
    threading.Thread(target=auto_seed_initial_data, name="auto-seed", daemon=True).start()


def auto_seed_initial_data():
    """
    Automatically checks if database is empty on startup.
    If empty, seeds 1000 customers, 15400 transactions, runs ML monitoring,
    prioritizes alerts, runs initial multi-agent investigations, and records
    evaluation benchmarks so the dashboard is 100% populated with enterprise-scale volume.
    """
    try:
        with get_db_context() as db:
            alert_count = db.scalar(select(func.count(Alert.id)))
            if alert_count and alert_count > 0:
                logger.info(f"Database already populated ({alert_count} alerts found). Skipping seed.")
                seed_state.update(ready=True, stage="ready")
                return
        seed_state["stage"] = "seeding"

        logger.info("Empty database detected. Auto-seeding enterprise AML simulation (15,400 txns, 1,000 entities)...")
        
        # 1. Generate Synthetic Data
        generator = SyntheticAMLDataGenerator(seed=42)
        with get_db_context() as db:
            generator.generate_and_seed_database(db, num_customers=1000, num_transactions=15400)
        logger.info("Seeded 1,000 customers, accounts, and 15,400 transactions.")

        # 2. Run Rule + Isolation Forest Transaction Monitoring
        with get_db_context() as db:
            alerts = transaction_monitor.scan_and_generate_alerts(db)
        logger.info(f"Generated {len(alerts)} alerts from dual transaction monitoring.")

        # 3. Triage & Prioritize Alerts
        with get_db_context() as db:
            ranked_alerts = alert_triage_service.prioritize_alerts(db, limit=200)
            ranked_ids = [a.alert_id for a in ranked_alerts]
            # Demo variety: one alert per showcase typology (India UPI mule, PAN structuring, ...,
            # plus an ML-only alert that typically ends in a documented NO_FILE decision).
            showcase = ["UPI_MULE_CHAIN", "STRUCTURING", "MULE_ACCOUNT", "LAYERING",
                        "FAN_OUT_DISPERSION", "ISOLATION_FOREST"]
            demo_ids = []
            for alert_type in showcase:
                a = db.query(Alert).filter(Alert.alert_type == alert_type).first()
                if a:
                    demo_ids.append(a.alert_id)
            demo_ids += [i for i in ranked_ids if i not in demo_ids]
        logger.info(f"Triaged and priority-ranked {len(ranked_ids)} alerts.")

        # 4. Auto-investigate 6 showcase alerts to populate investigation cases
        for idx, alert_id in enumerate(demo_ids[:6]):
            planner_mode = "adaptive" if idx % 2 == 0 else "static"
            try:
                execute_investigation_case(
                    case_id=f"CASE_{uuid.uuid4().hex[:8].upper()}",
                    alert_id=alert_id,
                    planner_mode=planner_mode,
                )
                logger.info(f"Auto-investigated sample case {idx+1}/6 for alert {alert_id} ({planner_mode} planner).")
            except Exception as e:
                logger.warning(f"Error investigating alert {alert_id}: {e}")

        # The dashboard, alerts and cases are usable from here; the evaluation continues afterwards.
        seed_state.update(ready=True, stage="evaluating")

        # 5. Run Initial Model Evaluation Benchmark on Held-Out Test Split
        try:
            with get_db_context() as db:
                # Kept small so the server starts quickly; POST /api/evaluation/run for a larger run.
                eval_res = evaluation_runner.run_benchmark_evaluation(db, split_type="TEST", seed=42, max_cases=64)
            f = eval_res["filing"]
            logger.info(f"Recorded evaluation: filing precision {f['precision']:.0%}, recall {f['recall']:.0%}, "
                        f"F1 {f['f1']:.2f} on {f['cases_investigated']} held-out alerts.")
        except Exception as e:
            logger.warning(f"Error recording evaluation benchmark: {e}")

        logger.info("Automatic database seeding completed successfully! Dashboard is now 100% populated.")
        seed_state["stage"] = "ready"

    except Exception as e:
        logger.error(f"Error during auto-seeding: {e}")
    finally:
        # Never leave the API stuck in "warming up": show whatever exists, honestly.
        seed_state["ready"] = True
        if seed_state["stage"] != "ready" and seed_state["stage"] != "evaluating":
            seed_state["stage"] = "ready"
