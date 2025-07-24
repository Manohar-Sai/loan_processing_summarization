from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from langgraph.graph import StateGraph, END
from agents.customer_agent import customer_interaction_agent
from agents.document_agent import document_processing_agent
from agents.eligibility_agent import eligibility_risk_assessment_agent
from agents.decision_agent import decision_recommendation_agent
from fastapi.middleware.cors import CORSMiddleware
from typing import TypedDict, Any, List


app = FastAPI(title="Gemini Loan Processor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoanState(TypedDict):
    name: str
    loan_type: str
    req_loan_amount: float
    cibil_score: Any
    income_monthly: Any
    asset_value: Any
    monthly_debt: Any
    
    eligible: Any
    reasons: Any
    policy_info: Any
    max_loan: Any
    sources: List[str]
    DTI: Any

    
    recommendation: str
    summary: str
    recommended_loan: int
    recommended_emi: Any
    applicable_rules: Any
    next_steps: Any
    updated_DTI: Any



graph = StateGraph(LoanState)

def customer_node(s: LoanState):
    print("stypid lag", s.keys())
    s["query"] = customer_interaction_agent(s["query"])
    return s

def eligibility_node(s: LoanState):
    applicant = {
        "loan_type": s["loan_type"],
        "income_monthly": s["income_monthly"],
        "cibil_score": s["cibil_score"],
        "monthly_debt": s["monthly_debt"],
    }
    if s['loan_type'] != 'personal':
        applicant |= {"asset_value": s["asset_value"],}
    result = eligibility_risk_assessment_agent(applicant)
    for key, value in result.items():
        s[key] = value
    return s

def decision_node(s: LoanState):
    # if not s["eligible"]:
    #     s["recommendation"] = None
    #     s["policy_sources"] = []
    #     return s
    res = decision_recommendation_agent(s)
    for key, value in res.items():
        s[key] = value
    return s

# creating graph nodes
graph.add_node("eligibility_node", eligibility_node)
graph.add_node("decision_node", decision_node)

# adding entry point and edges
graph.set_entry_point("eligibility_node")
graph.add_edge("eligibility_node", "decision_node")
graph.add_edge("decision_node", END)
workflow = graph.compile()


# app
@app.post("/process_loan/")
async def process_loan(
        name: str = Form(...),
        loan_type: str = Form(...),
        req_loan_amount: float = Form(...),
        monthly_debt: float = Form(...),
        cibil_report: UploadFile = File(...),
        salary_slips: List[UploadFile] = File(...), 
        property_doc: UploadFile = File(None),
        car_doc: UploadFile = File(None)
    ):
    if loan_type not in ("home", "personal", "car"):
        raise HTTPException(status_code=400, detail="Invalid loan_type")

    if len(salary_slips) < 1:
        raise HTTPException(status_code=400, detail="At least 1 salary slip file is required")

    if loan_type == "home" and property_doc is None:
        raise HTTPException(status_code=400, detail="Property document required for home loan")

    if loan_type == "car" and car_doc is None:
        raise HTTPException(status_code=400, detail="Car document required for car loan")

    salary_bytes = {slip.filename: await slip.read() for slip in salary_slips}
    cibil_bytes = {cibil_report.filename: await cibil_report.read()}
    asset_bytes = {}
    if loan_type == "home":
        asset_bytes = {property_doc.filename: await property_doc.read()}
    elif loan_type == "car":
        asset_bytes = {car_doc.filename: await car_doc.read()}

    # Extract via document agent
    doc_data = document_processing_agent(
        salary_slips=salary_bytes,
        cibil_pdf=cibil_bytes,
        asset_docs=asset_bytes
    )

    state = LoanState()
    state["name"] = name
    state["loan_type"] = loan_type
    state["income_monthly"] = doc_data["income_monthly"]
    state["cibil_score"] = doc_data["cibil_score"]
    state["asset_value"] = doc_data["asset_value"]
    state['monthly_debt'] = monthly_debt
    state['req_loan_amount'] = req_loan_amount

    state = workflow.invoke(state)

    return {
        # "customer_name": name,
        # "eligibility": state["eligibility"],
        # "recommendation": state["recommendation"],
        # # "policy_sources": state["policy_sources"]
        "output": state
    }

@app.get("/")
def root():
    return {"message": "multi-agent home loan API running!"}
