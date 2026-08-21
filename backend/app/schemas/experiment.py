from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime

class VariablesSchema(BaseModel):
    independent: list[str] = Field(default_factory=list, description="Variables manipulated in the experiment")
    dependent: list[str] = Field(default_factory=list, description="Variables measured in the experiment")
    control: list[str] = Field(default_factory=list, description="Variables held constant in the experiment")

class ExperimentBase(BaseModel):
    objective: str
    baseline: str
    treatment: str
    variables: VariablesSchema
    dataset: str
    metrics: list[str] = Field(default_factory=list)
    procedure: list[str] = Field(default_factory=list)
    expected_outcome: str
    measurable_success_criteria: str

class ExperimentCreate(ExperimentBase):
    hypothesis_id: UUID

class ExperimentOut(ExperimentBase):
    id: UUID
    hypothesis_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
