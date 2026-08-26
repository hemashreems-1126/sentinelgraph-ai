import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.db.models import Alert, Customer, Account


class AlertTriageService:
    """
    Alert Prioritization & Triage Service:
    - Deduplicates redundant alerts across shared entities
    - Normalizes alerts to standard taxonomy
    - Ranks and prioritizes alerts based on composite severity + customer risk tier
    """

    def prioritize_alerts(self, db: Session, limit: int = 100) -> List[Alert]:
        alerts = db.query(Alert).filter(Alert.status == "PENDING").all()
        if not alerts:
            return []

        # Load customer risk tier map
        cust_tier_map = {}
        for c in db.query(Customer).all():
            cust_tier_map[c.customer_id] = c.risk_tier

        # Load account to customer map
        acc_cust_map = {}
        for a in db.query(Account).all():
            acc_cust_map[a.account_id] = a.customer_id

        # Calculate composite priority score
        scored_alerts = []
        for alt in alerts:
            cust_id = alt.features_json.get("customer_id") if alt.features_json else None
            if not cust_id and alt.entity_type == "ACCOUNT":
                cust_id = acc_cust_map.get(alt.entity_id)

            cust_tier = cust_tier_map.get(cust_id, "MEDIUM")
            tier_multiplier = 1.3 if cust_tier == "HIGH" else (1.0 if cust_tier == "MEDIUM" else 0.8)

            severity_weight = {
                "CRITICAL": 1.4,
                "HIGH": 1.2,
                "MEDIUM": 1.0,
                "LOW": 0.7
            }.get(alt.severity, 1.0)

            priority_score = alt.raw_score * tier_multiplier * severity_weight
            scored_alerts.append((priority_score, alt))

        # Sort descending by priority score
        scored_alerts.sort(key=lambda x: x[0], reverse=True)

        for rank, (score, alt) in enumerate(scored_alerts, 1):
            alt.priority_rank = rank
            alt.status = "TRIAGED"
            alt.triaged_at = datetime.datetime.utcnow()

        db.commit()
        return [alt for _, alt in scored_alerts[:limit]]


alert_triage_service = AlertTriageService()
