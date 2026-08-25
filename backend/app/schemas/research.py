from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class ResearchSessionCreate(BaseModel):
    question_id: UUID
    budget: int = 5

class ResearchSessionOut(BaseModel):
    id: UUID
    question_id: UUID
    iteration: int
    budget: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
