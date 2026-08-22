import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.connection import Base

class ExperimentResult(Base):
    __tablename__ = "experiment_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, unique=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    metrics = Column(JSONB, nullable=False, default=dict)
    artifacts = Column(JSONB, nullable=False, default=list)
    status = Column(String, nullable=False)  # COMPLETED, FAILED
    execution_time_ms = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Evaluation fields
    verdict = Column(String, nullable=True)  # SUPPORTED, REJECTED, INCONCLUSIVE
    evaluation_summary = Column(Text, nullable=True)
    evaluation_confidence = Column(Float, nullable=True)
    evaluated_at = Column(DateTime(timezone=True), nullable=True)

    experiment = relationship("Experiment", back_populates="result")

