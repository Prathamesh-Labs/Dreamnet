from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Any

class HypothesisBase(BaseModel):
    statement: str
    rationale: str
    assumptions: list[str] = Field(default_factory=list)
    variables: list[str] = Field(default_factory=list)
    predicted_outcome: str
    confidence: float = 0.5
    testability: str = "MEDIUM"  # HIGH, MEDIUM, LOW

class HypothesisCreate(HypothesisBase):
    question_id: UUID

class HypothesisOut(HypothesisBase):
    id: UUID
    question_id: UUID
    status: str
    peer_review: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
