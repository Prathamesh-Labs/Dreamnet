# Import all the models here so that Alembic or SQLAlchemy can detect them
from app.database.connection import Base
from app.models.project import Project
from app.models.question import Question
from app.models.hypothesis import Hypothesis
