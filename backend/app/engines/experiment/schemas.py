from pydantic import BaseModel, Field

class VariablesOutput(BaseModel):
    independent: list[str] = Field(description="A list of independent variables that will be actively manipulated.")
    dependent: list[str] = Field(description="A list of dependent variables to be measured and monitored.")
    control: list[str] = Field(description="A list of control variables held constant throughout testing.")

class ExperimentEngineResponse(BaseModel):
    objective: str = Field(description="The core scientific objective of this experiment.")
    baseline: str = Field(description="The control setup or baseline configuration that represents current standard state.")
    treatment: str = Field(description="The experimental treatment or new methodology to apply.")
    variables: VariablesOutput = Field(description="The structured variables categorized into independent, dependent, and control.")
    dataset: str = Field(description="The scientific benchmark, dataset, or source data details used for tests.")
    metrics: list[str] = Field(description="The specific measurable quantitative metrics (e.g., latency, throughput, accuracy, loss).")
    procedure: list[str] = Field(description="Step-by-step reproducible instructions for running the experiment trial.")
    expected_outcome: str = Field(description="Detailed expectation and predicted qualitative/quantitative behavior.")
    measurable_success_criteria: str = Field(description="Exact, concrete target values or statistical thresholds determining whether the experiment supports the hypothesis.")
