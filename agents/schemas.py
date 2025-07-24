from pydantic import BaseModel, Field
from typing import List
from typing import Any

class DecisionOutput(BaseModel):
    summary: str
    recommendation: str

class CustomerOutput(BaseModel):
    loan_type: str
    cibil_score: int
    next_steps: List[str]
    income: float
    value: float
    existing_debt: float


class DocumentExtraction(BaseModel):
    income_monthly: float = Field(..., description="Annual income in INR")
    cibil_score: int = Field(..., description="CIBIL credit score (integer)")
    asset_value: float = Field(..., description="Property or car value in INR")


class PolicyThresholdsSchema(BaseModel):
    min_cibil: int
    max_dti: float
    interest_rate: float
    elegible_income: str
    income_threshold: str
    income_reasoning: str
    max_tenure: int
    min_tenure: int