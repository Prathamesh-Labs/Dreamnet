from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from uuid import UUID
from app.database.connection import get_db
from app.models.research_session import ResearchSession
from app.models.experiment import Experiment
from app.schemas.research import ResearchSessionCreate, ResearchSessionOut
from app.schemas.experiment import ExperimentOut
from app.research.controller import ResearchController
from app.services.research.report import ResearchReportGenerator


router = APIRouter()

@router.post("/research", response_model=ResearchSessionOut, status_code=status.HTTP_201_CREATED)
def create_research_session(payload: ResearchSessionCreate, db: Session = Depends(get_db)):
    try:
        # Check if active session already exists for this question
        existing = db.query(ResearchSession).filter(
            ResearchSession.question_id == payload.question_id,
            ResearchSession.status.in_(["IDLE", "RUNNING", "PAUSED"])
        ).first()
        if existing:
            return existing

        session = ResearchSession(
            question_id=payload.question_id,
            budget=payload.budget,
            status="IDLE"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.get("/research/{id}", response_model=ResearchSessionOut)
def get_research_session(id: UUID, db: Session = Depends(get_db)):
    session = db.query(ResearchSession).filter(ResearchSession.id == id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research session not found"
        )
    return session

@router.post("/research/{id}/start", response_model=ResearchSessionOut)
def start_research_session(id: UUID, db: Session = Depends(get_db)):
    try:
        session = ResearchController.start_session(id, db)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting research session: {str(e)}"
        )

@router.post("/research/{id}/pause", response_model=ResearchSessionOut)
def pause_research_session(id: UUID, db: Session = Depends(get_db)):
    try:
        session = ResearchController.pause_session(id, db)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/research/{id}/resume", response_model=ResearchSessionOut)
def resume_research_session(id: UUID, db: Session = Depends(get_db)):
    try:
        session = ResearchController.resume_session(id, db)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/research/{id}/stop", response_model=ResearchSessionOut)
def stop_research_session(id: UUID, db: Session = Depends(get_db)):
    try:
        session = ResearchController.stop_session(id, db)
        return session
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/experiments/{experiment_id}/approve", response_model=ExperimentOut)
def approve_experiment(experiment_id: UUID, db: Session = Depends(get_db)):
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found"
        )
    
    experiment.approved = True
    experiment.status = "READY"
    db.commit()

    # Find the active research session and resume it
    session = db.query(ResearchSession).filter(
        ResearchSession.question_id == experiment.hypothesis.question_id,
        ResearchSession.status == "PAUSED"
    ).first()

    if session:
        ResearchController.resume_session(session.id, db)

    db.refresh(experiment)
    return experiment

@router.get("/research/{id}/report", response_class=PlainTextResponse)
def get_research_session_report(id: UUID, db: Session = Depends(get_db)):
    try:
        report = ResearchReportGenerator.generate_markdown_report(id, db)
        return report
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error compiling report: {str(e)}"
        )

