import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, unique=True)
    verdict = Column(String, nullable=False) # SUPPORTED, REJECTED, INCONCLUSIVE
    evidence = Column(JSONB, nullable=False, default=list) # checklist array of assertions
    confidence = Column(Float, nullable=False)
    observations = Column(Text, nullable=True) # LLM observation interpretation explanation
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    experiment = relationship("Experiment", back_populates="evaluation")
