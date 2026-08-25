import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Discovery(Base):
    __tablename__ = "discoveries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_session_id = Column(UUID(as_uuid=True), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    observation = Column(Text, nullable=False)
    evidence = Column(JSONB, nullable=False, default=dict) # Key metric comparison dictionary
    supporting_experiments = Column(JSONB, nullable=False, default=list) # List of experiment IDs (strings)
    novelty_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    significance = Column(Float, nullable=False)
    reproducibility = Column(Float, nullable=False)
    recommended_action = Column(Text, nullable=True)
    status = Column(String, default="CANDIDATE", nullable=False) # CANDIDATE, VALIDATING, CONFIRMED, DISMISSED
    discovery_type = Column(String, nullable=True)
    source_experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="SET NULL"), nullable=True)
    expected_value = Column(Float, nullable=True)
    observed_value = Column(Float, nullable=True)
    deviation = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    research_session = relationship("ResearchSession")

    @property
    def question_id(self):
        if self.research_session:
            return self.research_session.question_id
        return None

