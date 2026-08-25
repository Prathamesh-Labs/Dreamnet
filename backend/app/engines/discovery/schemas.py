from pydantic import BaseModel
from typing import Any

class DetectedPattern(BaseModel):
    pattern_type: str  # unexpected_magnitude, unexpected_direction, contradiction, repeated_pattern, conditional
    title: str
    description: str
    evidence: dict[str, Any]
    supporting_experiments: list[str]
