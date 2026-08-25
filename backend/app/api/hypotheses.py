from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.database.connection import get_db
from app.schemas.experiment import ExperimentOut
from app.schemas.experiment_result import ExperimentResultOut
from app.schemas.evaluation import EvaluationOut
from app.models.experiment import Experiment
from app.models.experiment_result import ExperimentResult
from app.models.evaluation import Evaluation
from app.services.experiment.designer import ExperimentDesigner
from app.services.experiment.validator import ExperimentValidationError
from app.services.experiment.runner import ExperimentRunner
from app.services.experiment.evaluator import ExperimentEvaluator

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

@router.post("/experiments/{experiment_id}/run", response_model=ExperimentResultOut)
def run_hypothesis_experiment(experiment_id: UUID, db: Session = Depends(get_db)):
    try:
        result = ExperimentRunner.run_experiment(experiment_id, db)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing experiment: {str(e)}"
        )

@router.get("/experiments/{experiment_id}/results", response_model=ExperimentResultOut)
def get_experiment_results(experiment_id: UUID, db: Session = Depends(get_db)):
    try:
        result = db.query(ExperimentResult).filter(ExperimentResult.experiment_id == experiment_id).first()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment results not found."
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.post("/experiments/{experiment_id}/evaluate", response_model=EvaluationOut)
def evaluate_experiment_results(experiment_id: UUID, db: Session = Depends(get_db)):
    try:
        evaluation = ExperimentEvaluator.evaluate_experiment(experiment_id, db)
        return evaluation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating experiment: {str(e)}"
        )

@router.get("/experiments/{experiment_id}/evaluation", response_model=EvaluationOut)
def get_experiment_evaluation(experiment_id: UUID, db: Session = Depends(get_db)):
    try:
        evaluation = db.query(Evaluation).filter(Evaluation.experiment_id == experiment_id).first()
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evaluation results not found."
            )
        return evaluation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
