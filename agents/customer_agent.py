import json
from core.llm import get_gemini_llm
from agents.schemas import CustomerOutput

llm = get_gemini_llm()

def customer_interaction_agent(user_query: str) -> dict:
    prompt = (
        "You are a loan assistant. Identify loan_type (home/personal/car) and collect "
        "income, value (property/car or loan amount), existing_debt, cibil_score. "
        "Answer in JSON with keys: loan_type, income, value, existing_debt, cibil_score."
    )
    structured = llm.with_structured_output(CustomerOutput)
    resp = structured.invoke(prompt + "\nUser: " + user_query)
    return resp.model_dump()
