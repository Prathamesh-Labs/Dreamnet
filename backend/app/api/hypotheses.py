from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.database.connection import get_db
from app.schemas.experiment import ExperimentOut
from app.models.experiment import Experiment
from app.services.experiment.designer import ExperimentDesigner
from app.services.experiment.validator import ExperimentValidationError

router = APIRouter()

@router.post("/hypotheses/{hypothesis_id}/experiment", response_model=ExperimentOut, status_code=status.HTTP_201_CREATED)
def design_hypothesis_experiment(hypothesis_id: UUID, db: Session = Depends(get_db)):
    try:
        experiment = ExperimentDesigner.design_experiment(hypothesis_id, db)
        return experiment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ExperimentValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Experiment validation failed", "errors": e.errors}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to design experiment: {str(e)}"
        )

@router.get("/hypotheses/{hypothesis_id}/experiment", response_model=ExperimentOut)
def get_hypothesis_experiment(hypothesis_id: UUID, db: Session = Depends(get_db)):
    try:
        experiment = db.query(Experiment).filter(Experiment.hypothesis_id == hypothesis_id).first()
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment for hypothesis {hypothesis_id} not found."
            )
        return experiment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
