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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    question = relationship("Question", backref="hypotheses")
