# agents/decision_agent.py

from core.llm import get_gemini_llm
from core.rag import run_rag_query
from agents.schemas import DecisionOutput
import json
import math 


def calculate_emi(principal: float, annual_interest_rate: float, tenure_months: int) -> float:
    r = (annual_interest_rate / 12) / 100
    n = tenure_months
    if r == 0:
        return principal / n
    emi = (principal * r * ((1 + r) **   n)) / (((1 + r) ** n) - 1)
    return round(emi, 2)

def decision_recommendation_agent(data) -> dict:

    loan_type = data['loan_type']
    max_loan = data["max_loan"]
    interest_rate = data["policy_info"]["interest_rate"]
    max_dti = data["policy_info"]["max_dti"]
    max_tenure = data['policy_info']['max_tenure']
    # min_tenure = data['policy_sources']['min_tenure']
    # req_loan_amount = data["req_loan_amount"]
    llm = get_gemini_llm()
    rag_res = run_rag_query(
        llm=llm,
        query=f"what is the policy of {loan_type} loan",
    )

    llm_query = f'''
    You are a loan application expert
    
    Given the below policy:
    {rag_res['answer']}
     
    and also the follwing applicant data:
    {json.dumps(data)}

    Reveiw the data with the given policy and determine. Give a summary of the loan application. Also recommend the loan applicant about the next steps.

    Always ignore special characters in output.
    
    Example output: 
    {{'summary': (str, give overall summary),
      'recommendation': (str, just give the recommendation to get the loan)}}
'''.strip()
    
    structured = llm.with_structured_output(DecisionOutput)
    summary = structured.invoke(llm_query).model_dump()
    if not data['eligible']:
        decision = {
            'summary': summary['summary'],
            'recommendation': summary['recommendation'],
            'applicable_rules': [
            f"Minimum Cibil Score: {data['cibil_score']}",
            f"Income Criteria: {data["policy_info"]["income_threshold"]}",
            f"Max DTI Allowed: {max_dti}%",
            f"Max Tenure Available: {max_tenure} months",
            f"Interest Rate: {interest_rate}%",
        ]
        }
        return decision

    existing_debt = data['DTI']
    income = data['income_monthly']
        
 
    # Step 3: Adjust loan amount to respect DTI limits
    emi = calculate_emi(max_loan, interest_rate, max_tenure)
    total_dti = ((existing_debt + emi) / (income)) * 100 if income else 100
    flag = 0
    if existing_debt == 0:
        total_dti = ((emi) / (income)) * 100 if income else 100
        flag = 1

    # Reduce loan if DTI exceeds allowed policy
    if total_dti > max_dti:
        allowed_emi = (max_dti * (income) / 100) - existing_debt
        if allowed_emi > 0:
            max_loan = math.floor(max_loan * (allowed_emi / emi))
            emi = calculate_emi(max_loan, interest_rate, max_tenure)
            total_dti = ((existing_debt + emi) / (income)) * 100
            flag = 1
        

    decision = {
        'summary': summary['summary'],
        'recommendation': summary['recommendation'],
        'recommended_loan': max_loan,
        'recommended_emi': emi,
        'applicable_rules': [
            f"Interest Rate: {interest_rate}%",
            f"Max DTI Allowed: {max_dti}%",
            f"Max Tenure Available: {max_tenure} months",
        ],
        "next_steps": [
            "Sign loan agreement",
            "Submit original KYC documents",
            "Await disbursement",
        ],


    }
    if flag:
        decision |= {"updated_DTI": total_dti}
    return decision
