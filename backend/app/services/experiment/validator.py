from typing import Any

class ExperimentValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"Experiment validation failed: {', '.join(errors)}")

class ExperimentValidator:
    @staticmethod
    def validate(spec: dict[str, Any]) -> None:
        errors = []

        # Validate basic text fields
        text_fields = [
            "objective", "baseline", "treatment", "dataset", 
            "expected_outcome", "measurable_success_criteria"
        ]
        for field in text_fields:
            val = spec.get(field)
            if not val or not isinstance(val, str) or not val.strip():
                errors.append(f"Field '{field}' must be a non-empty string.")
            elif len(val.strip()) < 5:
                errors.append(f"Field '{field}' is too short (minimum 5 characters).")

        # Validate variables structure
        variables = spec.get("variables")
        if not variables or not isinstance(variables, dict):
            errors.append("Field 'variables' must be a dictionary.")
        else:
            for vtype in ["independent", "dependent", "control"]:
                vlist = variables.get(vtype)
                if not isinstance(vlist, list):
                    errors.append(f"Variables category '{vtype}' must be a list.")
                elif not vlist:
                    errors.append(f"Variables category '{vtype}' cannot be empty.")
                else:
                    for item in vlist:
                        if not isinstance(item, str) or not item.strip():
                            errors.append(f"Item in variables category '{vtype}' must be a non-empty string.")

        # Validate metrics
        metrics = spec.get("metrics")
        if not metrics or not isinstance(metrics, list):
            errors.append("Field 'metrics' must be a list.")
        elif not metrics:
            errors.append("Field 'metrics' cannot be empty.")
        else:
            for metric in metrics:
                if not isinstance(metric, str) or not metric.strip():
                    errors.append("Metric items must be non-empty strings.")

        # Validate procedure
        procedure = spec.get("procedure")
        if not procedure or not isinstance(procedure, list):
            errors.append("Field 'procedure' must be a list.")
        elif not procedure:
            errors.append("Field 'procedure' cannot be empty.")
        else:
            for step in procedure:
                if not isinstance(step, str) or not step.strip():
                    errors.append("Procedure steps must be non-empty strings.")

        if errors:
            raise ExperimentValidationError(errors)
