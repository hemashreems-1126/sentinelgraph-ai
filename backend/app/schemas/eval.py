import datetime
from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, List, Optional
from pydantic import Field


class EvaluationMetricsResponse(BaseModel):
    run_id: str
    timestamp: datetime.datetime
    split_type: str
    total_samples: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision_score: float
    recall_score: float
    f1_score: float
    accuracy_score: float
    roc_auc: float
    confusion_matrix_json: Dict[str, Any]
    classification_report_json: Dict[str, Any]
    metrics_json: Optional[Dict[str, Any]] = None
    dataset_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EvaluationTriggerRequest(BaseModel):
    split_type: str = "TEST"
    seed: int = 42
    max_cases: int = Field(default=120, ge=10, le=600, description="Alerts to fully investigate (stratified by type)")
