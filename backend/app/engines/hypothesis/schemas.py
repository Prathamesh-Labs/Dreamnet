from pydantic import BaseModel, Field

class SingleHypothesisOutput(BaseModel):
    statement: str = Field(description="Clear, falsifiable statement of the hypothesis.")
    rationale: str = Field(description="Scientific reasoning and explanation supporting the statement.")
    assumptions: list[str] = Field(description="A list of boundary assumptions required for this hypothesis to hold.")
    variables: list[str] = Field(description="Variables involved, such as independent/dependent parameters.")
    predicted_outcome: str = Field(description="Measurable and predicted empirical outcome of testing this hypothesis.")
    confidence: float = Field(description="Confidence estimate from 0.0 to 1.0.")
    testability: str = Field(description="Testability scale value: HIGH, MEDIUM, or LOW.")

class HypothesisEngineResponse(BaseModel):
    hypotheses: list[SingleHypothesisOutput] = Field(description="Exactly 3 competing and distinct scientific hypotheses.")
