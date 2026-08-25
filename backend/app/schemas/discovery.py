from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Any

class DiscoveryBase(BaseModel):
    title: str
    observation: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    supporting_experiments: list[str] = Field(default_factory=list)
    novelty_score: float
    confidence: float
    significance: float
    reproducibility: float
    recommended_action: str | None = None
    status: str

class DiscoveryOut(DiscoveryBase):
    id: UUID
    research_session_id: UUID
    question_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DiscoveryValidate(BaseModel):
    status: str  # CONFIRMED, DISMISSED, VALIDATING

class DiscoverySpawnLead(BaseModel):
    question_text: str
