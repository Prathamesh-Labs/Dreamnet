import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.connection import Base

class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("research_questions.id", ondelete="CASCADE"), nullable=False)
    iteration = Column(Integer, default=1, nullable=False)
    budget = Column(Integer, default=5, nullable=False)  # max iterations limit
    status = Column(String, default="IDLE", nullable=False)  # IDLE, RUNNING, PAUSED, STOPPED, COMPLETED
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    question = relationship("Question", back_populates="research_sessions")
