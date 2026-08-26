from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Alert, Transaction, Customer, InvestigationCase
from app.schemas.alert import AlertResponse, AlertGenerateRequest, AlertPrioritizeRequest
from app.services.data_generator import SyntheticAMLDataGenerator
from app.services.monitor import transaction_monitor
from app.services.triage import alert_triage_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=List[AlertResponse])
def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    split_type: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if split_type:
        query = query.filter(Alert.split_type == split_type)

    return query.order_by(Alert.priority_rank.asc(), Alert.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/stats/summary")
def get_alert_stats(db: Session = Depends(get_db)):
    total_alerts = db.query(Alert).count()
    pending_alerts = db.query(Alert).filter(Alert.status == "PENDING").count()
    triaged_alerts = db.query(Alert).filter(Alert.status == "TRIAGED").count()
    investigating_alerts = db.query(Alert).filter(Alert.status == "INVESTIGATING").count()
    closed_alerts = db.query(Alert).filter(Alert.status == "CLOSED").count()
    escalated_alerts = db.query(Alert).filter(Alert.status == "ESCALATED").count()

    total_customers = db.query(Customer).count()
    total_transactions = db.query(Transaction).count()
    fraud_txns = db.query(Transaction).filter(Transaction.is_fraud_injected == True).count()
    total_cases = db.query(InvestigationCase).count()

    # Alerts by type breakdown
    type_counts = {}
    for alt in db.query(Alert).all():
        type_counts[alt.alert_type] = type_counts.get(alt.alert_type, 0) + 1

    # Severity counts
    severity_counts = {
        "CRITICAL": db.query(Alert).filter(Alert.severity == "CRITICAL").count(),
        "HIGH": db.query(Alert).filter(Alert.severity == "HIGH").count(),
        "MEDIUM": db.query(Alert).filter(Alert.severity == "MEDIUM").count(),
        "LOW": db.query(Alert).filter(Alert.severity == "LOW").count()
    }

    return {
        "total_alerts": total_alerts,
        "pending_alerts": pending_alerts,
        "triaged_alerts": triaged_alerts,
        "investigating_alerts": investigating_alerts,
        "closed_alerts": closed_alerts,
        "escalated_alerts": escalated_alerts,
        "total_customers": total_customers,
        "total_transactions": total_transactions,
        "fraud_transactions": fraud_txns,
        "total_cases_investigated": total_cases,
        "alert_type_breakdown": type_counts,
        "severity_breakdown": severity_counts
    }


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: str, db: Session = Depends(get_db)):
    alt = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alt:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alt


@router.post("/generate")
def generate_synthetic_alerts(
    req: AlertGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Phase 1, Step 1: Generates synthetic transactions and runs monitoring detection to populate alerts.
    """
    generator = SyntheticAMLDataGenerator(seed=req.seed)
    gen_stats = generator.generate_and_seed_database(
        db,
        num_customers=req.num_customers,
        num_transactions=req.num_transactions
    )
    alerts = transaction_monitor.scan_and_generate_alerts(db)

    return {
        "message": f"Successfully generated synthetic dataset and detected {len(alerts)} alerts.",
        "generation_stats": gen_stats,
        "alerts_generated_count": len(alerts)
    }


@router.post("/prioritize", response_model=List[AlertResponse])
def prioritize_alerts(
    req: AlertPrioritizeRequest,
    db: Session = Depends(get_db)
):
    """
    Phase 1, Step 2: Normalizes, deduplicates, and ranks alerts by priority.
    """
    triaged = alert_triage_service.prioritize_alerts(db, limit=req.batch_size or 100)
    return triaged
