from sqlalchemy.orm import Session
from app.models.hypothesis import Hypothesis
from app.models.experiment import Experiment
from app.services.llm.factory import LLMProviderFactory
from app.services.experiment.validator import ExperimentValidator
from typing import Any

class ExperimentDesigner:
    @staticmethod
    def design_experiment(hypothesis_id: Any, db: Session) -> Experiment:
        # Fetch the hypothesis
        hypothesis = db.query(Hypothesis).filter(Hypothesis.id == hypothesis_id).first()
        if not hypothesis:
            raise ValueError(f"Hypothesis with ID {hypothesis_id} not found.")

        # Prepare hypothesis dictionary for the provider
        hypothesis_dict = {
            "statement": hypothesis.statement,
            "rationale": hypothesis.rationale,
            "assumptions": hypothesis.assumptions or [],
            "variables": hypothesis.variables or [],
            "predicted_outcome": hypothesis.predicted_outcome
        }

        # Resolve LLM provider and generate experiment
        provider = LLMProviderFactory.get_provider()
        spec = provider.design_experiment(hypothesis_dict)

        # Validate the generated specification
        ExperimentValidator.validate(spec)

        # Remove any existing experiment for this hypothesis first (to update/regenerate)
        db.query(Experiment).filter(Experiment.hypothesis_id == hypothesis.id).delete()

        # Save to database
        db_experiment = Experiment(
            hypothesis_id=hypothesis.id,
            objective=spec.get("objective"),
            baseline=spec.get("baseline"),
            treatment=spec.get("treatment"),
            variables=spec.get("variables"),
            dataset=spec.get("dataset"),
            metrics=spec.get("metrics"),
            procedure=spec.get("procedure"),
            expected_outcome=spec.get("expected_outcome"),
            measurable_success_criteria=spec.get("measurable_success_criteria"),
            status="READY"  # Default status for validated experiments is READY
        )

        db.add(db_experiment)
        db.commit()
        db.refresh(db_experiment)

        return db_experiment
