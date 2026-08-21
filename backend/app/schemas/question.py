from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class QuestionBase(BaseModel):
    text: str
    project_id: UUID | None = None
    status: str | None = "active"

class QuestionCreate(QuestionBase):
    pass

class QuestionOut(QuestionBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
