from typing import Dict, Any
import math
import json
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
    loan_type = applicant_data.get('loan_type', 'personal')
    income = float(applicant_data.get("income_monthly", 0))
    cibil = int(applicant_data.get("cibil_score", 0))
    existing_monthly_debt = float(applicant_data.pop("existing_debt")) if "existing_debt" in applicant_data else 0

    llm = get_gemini_llm()

    rag_query = f'''
    You are a loan application expert

    Give {loan_type} loan policy CIBIL, DTI, interest rate, monthly income requirements, max and min tenure of the loan in numbers.

    Instructions:
    - Always extract DTI in percentage without percentage symbol.
'''.strip()


    rag_res = run_rag_query(
        llm=llm,
        query= rag_query,
    )

    # Extract thresholds using structured output
    llm_query = f'''
    You are a loan application expert
    
    Extract min_cibil, max_dti, income_threshold, interest_rate, max_tenure and min_tenure in months from below policy:
    {rag_res['answer']}
     
    Consider the follwing applicant data:
    {json.dumps(applicant_data)}
    Reveiw the data with the given policy and determine whether the applicant is eligible (Yes/No) with the key eligible_income. Give the reasoning for eligible_income decision with key income_reasoning
    

    Always ignore special characters in output.

    Example output: 
    {{'min_cibil': int, 
     'max_dti': float, 
     'max_tenure': int,
     'min_tenure': int,
     'interest_rate': float, 
     'income_threshold': str, 
     'eligible_income': 'Yes/No', 
     'income_reasoning': 'reasoning'/}}
'''.strip()
    
    structured = llm.with_structured_output(PolicyThresholdsSchema)
    thresholds = structured.invoke(llm_query).model_dump()
    if thresholds["max_tenure"] < 12:
        thresholds["max_tenure"] = thresholds["max_tenure"] *12
    if thresholds["min_tenure"] < 12:
        thresholds["min_tenure"] = thresholds["max_tenure"] *12
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
    if income > 0:
        dti = ((existing_monthly_debt / (income))*100)
    else:
        dti = 100

    result |= {"DTI": round(dti, 2)}

    # 1. CIBIL score check
    if cibil < min_cibil:
        result["eligible"] = False
        result["reasons"].append(
            f"CIBIL {cibil} < required minimum {min_cibil}"
        )
        return result

    # 2. DTI check
    print(dti)
    if dti > max_dti:
        result["eligible"] = False
        result["reasons"].append(f"DTI {dti:.1f}% > allowed {max_dti}%")
        return result

    # 3. Loan-to-Value checks for secured loans
    if loan_type in ("home", "car"):   
        property_value = float(applicant_data.get("asset_value", 0))
        if property_value <= 0:
            result["eligible"] = False
            result["reasons"].append(
                f"No {'property' if loan_type=='home' else 'car'} value provided"
            )
            return result

        ltv_limit = 0.7 if loan_type == "home" else 0.8
        result["max_loan"] = property_value * ltv_limit
    else:
        result["max_loan"] = income * 12 * 0.2
    
    if thresholds['elegible_income'] == 'No':
        result["eligible"] = False
        result["reasons"].append(thresholds['income_reasoning'])
        result['max_loan'] = 0
        return result
    else:
        result.pop('reasons')
    
    return result