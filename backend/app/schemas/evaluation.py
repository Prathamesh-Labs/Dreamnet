from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Any

class EvaluationBase(BaseModel):
    verdict: str  # SUPPORTED, REJECTED, INCONCLUSIVE
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float
    observations: str | None = None

class EvaluationOut(EvaluationBase):
    id: UUID
    experiment_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
