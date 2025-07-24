from pydantic import BaseModel, Field
from typing import List

class DecisionOutput(BaseModel):
    summary: str
    recommended_loan: float
    tenure_months: int
    emi: float
    dti_percent: float
    applicable_rules: list
    next_steps: list
    # summary: str
    # applicable_rules: List[str]
    # next_steps: List[str]
    # recommended_loan: float
    # emi: float
    # dti_percent: float

class CustomerOutput(BaseModel):
    loan_type: str
    cibil_score: int
    next_steps: List[str]
    income: float
    value: float
    existing_debt: float


class DocumentExtraction(BaseModel):
    income_annual: float = Field(..., description="Annual income in INR")
    cibil_score: int = Field(..., description="CIBIL credit score (integer)")
    asset_value: float = Field(..., description="Property or car value in INR")


class PolicyThresholdsSchema(BaseModel):
    min_cibil: int
    max_dti: float
    interest_rate: float