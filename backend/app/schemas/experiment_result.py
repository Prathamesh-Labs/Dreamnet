from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Any

class ExperimentResultBase(BaseModel):
    metrics: dict[str, Any] = Field(default_factory=dict)
    raw_output: str | None = None
    artifacts: list[Any] = Field(default_factory=list)
    execution_time_ms: float

class ExperimentResultOut(ExperimentResultBase):
    id: UUID
    experiment_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
