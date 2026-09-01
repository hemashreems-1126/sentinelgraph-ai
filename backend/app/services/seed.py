import logging
from sqlalchemy import select, func
from app.db.session import get_db_context
from app.db.models import Alert
from app.services.data_generator import SyntheticAMLDataGenerator
from app.services.monitor import transaction_monitor
from app.services.triage import alert_triage_service
from app.agents.workflow import execute_investigation_case
from app.utils.evaluation_runner import evaluation_runner

logger = logging.getLogger("SentinelGraph.Seed")


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
                return

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
            ranked_alerts = alert_triage_service.prioritize_alerts(db, batch_size=200)
        logger.info(f"Triaged and priority-ranked {len(ranked_alerts)} alerts.")

        # 4. Auto-investigate Top 6 Alerts to populate investigation cases
        top_alerts = ranked_alerts[:6]
        for idx, alert in enumerate(top_alerts):
            planner_mode = "adaptive" if idx % 2 == 0 else "static"
            try:
                execute_investigation_case(alert.alert_id, planner_mode=planner_mode)
                logger.info(f"Auto-investigated sample case {idx+1}/6 for alert {alert.alert_id} ({planner_mode} planner).")
            except Exception as e:
                logger.warning(f"Error investigating alert {alert.alert_id}: {e}")

        # 5. Run Initial Model Evaluation Benchmark on Held-Out Test Split
        try:
            with get_db_context() as db:
                eval_res = evaluation_runner.run_benchmark_evaluation(db, split_type="TEST", seed=42)
            logger.info(f"Auto-recorded benchmark evaluation (Fraud Recall: {eval_res['recall_score']*100:.1f}%).")
        except Exception as e:
            logger.warning(f"Error recording evaluation benchmark: {e}")

        logger.info("Automatic database seeding completed successfully! Dashboard is now 100% populated.")

    except Exception as e:
        logger.error(f"Error during auto-seeding: {e}")
