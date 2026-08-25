import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Hypothesis(Base):
    __tablename__ = "hypotheses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("research_questions.id", ondelete="CASCADE"), nullable=False)
    statement = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    assumptions = Column(JSONB, nullable=False, default=list)
    variables = Column(JSONB, nullable=False, default=list)
    predicted_outcome = Column(Text, nullable=False)
    confidence = Column(Float, default=0.5)
    testability = Column(String, default="MEDIUM")  # HIGH, MEDIUM, LOW
    status = Column(String, default="PROPOSED")  # PROPOSED, SUPPORTED, REJECTED, INCONCLUSIVE
    peer_review = Column(JSONB, nullable=False, default=list)
    parent_discovery_id = Column(UUID(as_uuid=True), ForeignKey("discoveries.id", ondelete="SET NULL"), nullable=True)
    parent_experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    question = relationship("Question", backref="hypotheses")
    experiment = relationship("Experiment", back_populates="hypothesis", uselist=False, cascade="all, delete-orphan", foreign_keys="[Experiment.hypothesis_id]")


