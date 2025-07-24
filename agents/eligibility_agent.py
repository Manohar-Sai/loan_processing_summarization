from typing import Dict, Any
import math
from core.rag import run_rag_query
from core.llm import get_gemini_llm
from agents.schemas import PolicyThresholdsSchema

def eligibility_risk_assessment_agent(applicant_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate eligibility for a home loan based on:
    - Income and property value (for Loan-to-Value)
    - CIBIL score threshold
    - Debt-to-Income ratio limit
    Returns structured results with eligibility status, recommended loan, and detailed metrics.
    """
    print(applicant_data)
    loan_type = applicant_data.get('loan_type', 'personal')
    income = float(applicant_data.get("income", 0))
    cibil = int(applicant_data.get("cibil_score", 0))
    existing_monthly_debt = float(applicant_data.get("existing_debt", 0))
    

    llm = get_gemini_llm()
    rag_res = run_rag_query(
        llm=llm,
        query=f"Give {loan_type} loan policy CIBIL, DTI, and interest rate requirements in numbers. Always extract DTI in percentage without percentage symbol.",
    )

    # Extract thresholds using structured output
    structured = llm.with_structured_output(PolicyThresholdsSchema)
    thresholds = structured.invoke(
        f"Extract min_cibil, max_dti, and interest_rate from:\n\n{rag_res['answer']}"
    ).model_dump()

    min_cibil = thresholds.get("min_cibil", 700)
    max_dti = thresholds.get("max_dti", 50.0)
    interest_rate = thresholds.get("interest_rate", 10.0)
    result = {
        "eligible": True,
        "reasons": [],
        "max_loan": 0.0,
        "policy_info": thresholds,
        "sources": rag_res["sources"],
    }

    # 1. CIBIL score check
    if cibil < min_cibil:
        result["eligible"] = False
        result["reasons"].append(
            f"CIBIL {cibil} < required minimum {min_cibil}"
        )
        return result

    # 2. DTI check
    dti = ((existing_monthly_debt / (income/12))*100) if income else 1
    print(dti)
    if dti > max_dti:
        result["eligible"] = False
        result["reasons"].append(f"DTI {dti:.1f}% > allowed {max_dti}%")
        return result

    # 3. Loan-to-Value checks for secured loans
    if loan_type in ("home", "car"):   
        property_value = float(applicant_data.get("property_value", 0))
        if property_value <= 0:
            result["eligible"] = False
            result["reasons"].append(
                f"No {'property' if loan_type=='home' else 'car'} value provided"
            )
            return result

        ltv_limit = 0.9 if loan_type == "home" else 0.8
        result["max_loan"] = property_value * ltv_limit
    else:
        result["max_loan"] = income * 0.2

    result |= {"cibil score": cibil,
               "DTI": round(dti, 2)}
    return result