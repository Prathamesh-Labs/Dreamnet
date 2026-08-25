from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.database.connection import get_db
from app.models.question import Question
from app.models.hypothesis import Hypothesis
from app.schemas.question import QuestionCreate, QuestionOut
from app.schemas.hypothesis import HypothesisOut
from app.services.llm.factory import LLMProviderFactory

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
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error registering question: {str(e)}"
        )

    # Generate hypotheses automatically after question is successfully created
    try:
        provider = LLMProviderFactory.get_provider()
        hypotheses_data = provider.generate_hypotheses(db_question.text)
        for h_data in hypotheses_data:
            review_dialogue = provider.simulate_peer_review(db_question.text, h_data.get("statement"))
            db_h = Hypothesis(
                question_id=db_question.id,
                statement=h_data.get("statement"),
                rationale=h_data.get("rationale"),
                assumptions=h_data.get("assumptions", []),
                variables=h_data.get("variables", []),
                predicted_outcome=h_data.get("predicted_outcome"),
                confidence=h_data.get("confidence", 0.5),
                testability=h_data.get("testability", "MEDIUM"),
                status="PROPOSED",
                peer_review=review_dialogue
            )
            db.add(db_h)
        db.commit()
    except Exception as e:
        # Don't fail the question creation if hypothesis generation fails, just log it
        print(f"[create_question] Warning: Hypothesis generation failed: {e}")
        db.rollback()

    return db_question

@router.get("/questions", response_model=list[QuestionOut])
def list_questions(db: Session = Depends(get_db)):
    try:
        return db.query(Question).order_by(Question.created_at.desc()).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.get("/questions/{question_id}/hypotheses", response_model=list[HypothesisOut])
def get_question_hypotheses(question_id: UUID, db: Session = Depends(get_db)):
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        return db.query(Hypothesis).filter(Hypothesis.question_id == question_id).all()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.post("/questions/{question_id}/hypotheses/generate", response_model=list[HypothesisOut])
def generate_question_hypotheses(question_id: UUID, db: Session = Depends(get_db)):
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )

        # Delete existing hypotheses
        db.query(Hypothesis).filter(Hypothesis.question_id == question_id).delete()

        # Generate new hypotheses
        provider = LLMProviderFactory.get_provider()
        hypotheses_data = provider.generate_hypotheses(question.text)
        new_hypotheses = []
        for h_data in hypotheses_data:
            review_dialogue = provider.simulate_peer_review(question.text, h_data.get("statement"))
            db_h = Hypothesis(
                question_id=question.id,
                statement=h_data.get("statement"),
                rationale=h_data.get("rationale"),
                assumptions=h_data.get("assumptions", []),
                variables=h_data.get("variables", []),
                predicted_outcome=h_data.get("predicted_outcome"),
                confidence=h_data.get("confidence", 0.5),
                testability=h_data.get("testability", "MEDIUM"),
                status="PROPOSED",
                peer_review=review_dialogue
            )
            db.add(db_h)
            new_hypotheses.append(db_h)
        db.commit()
        for h in new_hypotheses:
            db.refresh(h)
        return new_hypotheses
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating hypotheses: {str(e)}"
        )

