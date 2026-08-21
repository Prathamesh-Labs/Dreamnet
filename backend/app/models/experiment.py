import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hypothesis_id = Column(UUID(as_uuid=True), ForeignKey("hypotheses.id", ondelete="CASCADE"), nullable=False, unique=True)
    objective = Column(Text, nullable=False)
    baseline = Column(Text, nullable=False)
    treatment = Column(Text, nullable=False)
    variables = Column(JSONB, nullable=False)  # {"independent": [...], "dependent": [...], "control": [...]}
    dataset = Column(Text, nullable=False)
    metrics = Column(JSONB, nullable=False)  # list of strings
    procedure = Column(JSONB, nullable=False)  # list of strings
    expected_outcome = Column(Text, nullable=False)
    measurable_success_criteria = Column(Text, nullable=False)
    status = Column(String, default="DRAFT")  # DRAFT, READY, RUNNING, COMPLETED, FAILED
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    hypothesis = relationship("Hypothesis", back_populates="experiment")
