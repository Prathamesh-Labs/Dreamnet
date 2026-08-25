import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Question(Base):
    __tablename__ = "research_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    text = Column(Text, nullable=False)
    status = Column(String, default="active")  # active, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    project = relationship("Project", backref="research_questions")
    research_sessions = relationship("ResearchSession", back_populates="question", cascade="all, delete-orphan")


