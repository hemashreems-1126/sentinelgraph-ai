import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any


class AlertBase(BaseModel):
    entity_type: str = "TRANSACTION"
    entity_id: str
    alert_type: str
    severity: str = "MEDIUM"
    raw_score: float = 50.0
    priority_rank: int = 1
    trigger_reason: str
    features_json: Optional[Dict[str, Any]] = None
    split_type: str = "TRAIN"


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: int
    alert_id: str
    status: str
    created_at: datetime.datetime
    triaged_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AlertPrioritizeRequest(BaseModel):
    batch_size: Optional[int] = 100


class AlertGenerateRequest(BaseModel):
    num_customers: int = Field(default=200, ge=10, le=2000)
    num_transactions: int = Field(default=1500, ge=50, le=10000)
    seed: int = 42
