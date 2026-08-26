from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import EvaluationMetricRecord
from app.schemas.eval import EvaluationMetricsResponse, EvaluationTriggerRequest
from app.utils.evaluation_runner import evaluation_runner

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.get("/latest", response_model=EvaluationMetricsResponse)
def get_latest_evaluation(db: Session = Depends(get_db)):
    record = db.query(EvaluationMetricRecord).order_by(EvaluationMetricRecord.timestamp.desc()).first()
    if not record:
        # Run a benchmark if none exists
        res = evaluation_runner.run_benchmark_evaluation(db, split_type="TEST", seed=42)
        record = db.query(EvaluationMetricRecord).filter(EvaluationMetricRecord.run_id == res["run_id"]).first()

    return record


@router.get("/history", response_model=List[EvaluationMetricsResponse])
def get_evaluation_history(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    return db.query(EvaluationMetricRecord).order_by(EvaluationMetricRecord.timestamp.desc()).limit(limit).all()


@router.post("/run", response_model=EvaluationMetricsResponse)
def trigger_evaluation(
    req: EvaluationTriggerRequest,
    db: Session = Depends(get_db)
):
    """
    Executes model evaluation against the synthetic test set, generating precision, recall, F1, and confusion matrix.
    """
    res = evaluation_runner.run_benchmark_evaluation(db, split_type=req.split_type, seed=req.seed)
    record = db.query(EvaluationMetricRecord).filter(EvaluationMetricRecord.run_id == res["run_id"]).first()
    return record
