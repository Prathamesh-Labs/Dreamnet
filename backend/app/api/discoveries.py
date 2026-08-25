from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.database.connection import get_db
from app.models.discovery import Discovery
from app.models.question import Question
from app.models.research_session import ResearchSession
from app.schemas.discovery import DiscoveryOut, DiscoveryValidate, DiscoverySpawnLead
from app.schemas.question import QuestionOut
from app.engines.discovery.analyzer import DiscoveryAnalyzer

router = APIRouter()

@router.post("/research/{id}/discover", response_model=list[DiscoveryOut])
def trigger_discovery_analysis(id: UUID, db: Session = Depends(get_db)):
    try:
        discoveries = DiscoveryAnalyzer.analyze_session_for_discoveries(id, db)
        return discoveries
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing discovery analysis: {str(e)}"
        )

@router.get("/research/{id}/discoveries", response_model=list[DiscoveryOut])
def get_session_discoveries(id: UUID, db: Session = Depends(get_db)):
    try:
        return db.query(Discovery).filter(Discovery.research_session_id == id).order_by(Discovery.created_at.desc()).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.get("/discoveries", response_model=list[DiscoveryOut])
def list_discoveries(db: Session = Depends(get_db)):
    try:
        return db.query(Discovery).order_by(Discovery.created_at.desc()).all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.get("/discoveries/{id}", response_model=DiscoveryOut)
def get_discovery_details(id: UUID, db: Session = Depends(get_db)):
    discovery = db.query(Discovery).filter(Discovery.id == id).first()
    if not discovery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discovery candidate not found"
        )
    return discovery

@router.post("/discoveries/{id}/validate", response_model=DiscoveryOut)
def validate_discovery_candidate(id: UUID, payload: DiscoveryValidate, db: Session = Depends(get_db)):
    discovery = db.query(Discovery).filter(Discovery.id == id).first()
    if not discovery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discovery candidate not found"
        )
    
    discovery.status = payload.status
    db.commit()
    db.refresh(discovery)
    return discovery

@router.post("/discoveries/{id}/spawn_lead", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
def spawn_research_lead(id: UUID, payload: DiscoverySpawnLead, db: Session = Depends(get_db)):
    discovery = db.query(Discovery).filter(Discovery.id == id).first()
    if not discovery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discovery candidate not found"
        )

    # Validate that the discovery is CONFIRMED before spawning a lead
    if discovery.status != "CONFIRMED":
        discovery.status = "CONFIRMED" # Auto-validate if validation step was skipped

    db_question = Question(
        text=payload.question_text,
        status="active"
    )
    
    try:
        db.add(db_question)
        db.commit()
        db.refresh(db_question)

        # Automatically seed a ResearchSession for the child question
        db_session = ResearchSession(
            question_id=db_question.id,
            budget=5,
            status="IDLE"
        )
        db.add(db_session)
        db.commit()
        
        # Link child question ID back to the discovery's recommended action or title for trace references if wanted
        discovery.recommended_action = f"Child Question Spawned: {db_question.id}"
        db.commit()

        return db_question
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error spawning research question lead: {str(e)}"
        )
