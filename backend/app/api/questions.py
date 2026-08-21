from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.question import Question
from app.schemas.question import QuestionCreate, QuestionOut

router = APIRouter()

@router.post("/questions", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
def create_question(question_in: QuestionCreate, db: Session = Depends(get_db)):
    db_question = Question(
        text=question_in.text,
        project_id=question_in.project_id,
        status=question_in.status or "active"
    )
    try:
        db.add(db_question)
        db.commit()
        db.refresh(db_question)
        return db_question
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.get("/questions", response_model=list[QuestionOut])
def list_questions(db: Session = Depends(get_db)):
    try:
        return db.query(Question).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
