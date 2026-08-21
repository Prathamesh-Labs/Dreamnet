from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Any

class ExperimentResultBase(BaseModel):
    stdout: str | None = None
    stderr: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[str] = Field(default_factory=list)
    status: str  # COMPLETED, FAILED
    execution_time_ms: float

class ExperimentResultOut(ExperimentResultBase):
    id: UUID
    experiment_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
