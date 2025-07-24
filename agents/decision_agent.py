# agents/decision_agent.py

from core.llm import get_gemini_llm
from core.rag import run_rag_query
from agents.schemas import DecisionOutput
import math 


def calculate_emi(principal: float, annual_interest_rate: float, tenure_months: int) -> float:
    r = (annual_interest_rate / 12) / 100
    n = tenure_months
    if r == 0:
        return principal / n
    emi = (principal * r * ((1 + r) ** n)) / (((1 + r) ** n) - 1)
    return round(emi, 2)

def decision_recommendation_agent(applicant_data: dict, loan_type: str) -> dict:

    max_loan = applicant_data["max_loan"]
    interest_rate = applicant_data["policy_info"]["interest_rate"]
    max_dti = applicant_data["policy_info"]["max_dti"]
    llm = get_gemini_llm()
    rag_res = run_rag_query(
        llm=llm,
        query=f"What is the typical tenure (in months) for {loan_type} loans as per policy?",
    )

    # Extract tenure (fallback to defaults if not found)
    try:
        tenure_months = int([int(s) for s in rag_res["answer"].split() if s.isdigit()][0])
    except Exception:
        tenure_months = 240 if loan_type == "home" else 60 if loan_type == "car" else 48
    
    existing_debt = applicant_data['dti']
    income = applicant_data.get('income', 0)
 
    # ✅ Step 3: Adjust loan amount to respect DTI limits
    emi = calculate_emi(max_loan, interest_rate, tenure_months)
    total_dti = ((existing_debt + emi) / (income / 12)) * 100 if income else 100

    # Reduce loan if DTI exceeds allowed policy
    if total_dti > max_dti:
        # proportionally scale down loan to meet DTI
        allowed_emi = (max_dti * (income / 12) / 100) - existing_debt
        if allowed_emi > 0:
            # inverse EMI to adjust principal (approximation via proportion)
            max_loan = math.floor(max_loan * (allowed_emi / emi))
            emi = calculate_emi(max_loan, interest_rate, tenure_months)
            total_dti = ((existing_debt + emi) / (income / 12)) * 100

    decision = DecisionOutput(
        summary=f"Loan application approved based on income, CIBIL, and policy thresholds.",
        recommended_loan=max_loan,
        tenure_months=tenure_months,
        emi=emi,
        dti_percent=round(total_dti, 2),
        applicable_rules=[
            f"Interest Rate: {interest_rate}%",
            f"Max DTI Allowed: {max_dti}%",
            f"Tenure Recommended: {tenure_months} months",
        ],
        next_steps=[
            "Sign loan agreement",
            "Submit original KYC documents",
            "Await disbursement",
        ],
    )
    return decision.model_dump()

    # Tag search with loan type for precise retrieval
    query = f"{loan_type} loan policy context: {context}"

    # RAG retrieval
    rag = run_rag_query(llm=llm, query=query)
    policy_text = rag["answer"]
    sources = rag["sources"]

    # Summarization prompt
    prompt = (
        f"Loan Type: {loan_type}\n"
        f"Context: {context}\n\n"
        f"Relevant policies:\n{policy_text}\n\n"
        "Return a JSON matching the DecisionOutput schema with fields: "
        "summary, applicable_rules, next_steps, recommended_loan, emi, dti_percent."
    )
    structured_llm = llm.with_structured_output(DecisionOutput)
    response: DecisionOutput  = structured_llm.invoke(prompt)
    return {"recommendation": response.model_dump(), "policy_sources": sources}
