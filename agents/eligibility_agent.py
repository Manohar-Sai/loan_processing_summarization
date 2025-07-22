from typing import Dict, Any
import math

def eligibility_risk_assessment_agent(applicant_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate eligibility for a home loan based on:
    - Income and property value (for Loan-to-Value)
    - CIBIL score threshold
    - Debt-to-Income ratio limit
    Returns structured results with eligibility status, recommended loan, and detailed metrics.
    """
    income = float(applicant_data.get("income", 0))
    property_value = float(applicant_data.get("property_value", 0))
    cibil = int(applicant_data.get("cibil_score", 0))
    existing_monthly_debt = float(applicant_data.get("existing_monthly_debt", 0))
    
    # Constants & thresholds
    CIBIL_MIN = 725
    DTI_MAX = 0.50 
    LTV_MAX = 0.90  
    # up to 90% of property value :contentReference[oaicite:2]{index=2}

    recommended_loan = min(property_value * LTV_MAX, income * 6)  # also cap by ~6× annual income :contentReference[oaicite:3]{index=3}

    # Estimate proposed monthly EMI at 7% annual interest over 20 years
    principal = recommended_loan
    monthly_rate = 0.07 / 12
    n = 20 * 12
    emi = principal * monthly_rate * (math.pow(1 + monthly_rate, n)) / (math.pow(1 + monthly_rate, n) - 1)
    
    # Compute DTI (existing debt + EMI) / gross income
    monthly_income = income / 12
    dti = (existing_monthly_debt + emi) / monthly_income if monthly_income > 0 else 1.0
    
    # Evaluate eligibility
    eligible = (
        cibil >= CIBIL_MIN and
        dti <= DTI_MAX and
        property_value > 0 and
        income > 0
    )
    
    return {
        "eligible": eligible,
        "cibil": cibil,
        "cibil_minimum": CIBIL_MIN,
        "dti": round(dti * 100, 2),
        "dti_maximum": DTI_MAX * 100,
        "emi": round(emi, 2),
        "recommended_loan": round(recommended_loan, 2),
        "ltv_maximum_percent": LTV_MAX * 100
    }
