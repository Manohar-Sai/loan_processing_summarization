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
    file_bytes: bytes
    filename: str
    query: str
    doc_data: Any
    eligibility: Any
    recommendation: str
    policy_sources: List[str]
    loan_type: str
    income_annual: Any
    cibil_score: Any
    asset_value: Any
    monthly_debt: Any

graph = StateGraph(LoanState)

# @graph.node
def customer_node(s: LoanState):
    print("stypid lag", s.keys())
    s["query"] = customer_interaction_agent(s["query"])
    # print('customer-------',s)
    return s

# @graph.node
# def document_node(s: LoanState):
#     s["doc_data"] = document_processing_agent_multimodal(
#         file_bytes=s["file_bytes"],
#         filename=s["filename"]
#     )
#     # print('document----------',s)
#     return s

# @graph.node
def eligibility_node(s: LoanState):
    applicant = {
        "loan_type": s["loan_type"],
        "income": s["income_annual"],
        "cibil_score": s["cibil_score"],
        "existing_debt": s["monthly_debt"],  # or include DTI logic if desired
    }
    if s['loan_type'] != 'personal':
        applicant |= {"asset_value": s["asset_value"],}
    s["eligibility"] = eligibility_risk_assessment_agent(applicant)
    return s

# @graph.node
def decision_node(s: LoanState):
    if not s["eligibility"].get("eligible", False):
        s["recommendation"] = None
        s["policy_sources"] = []
        return s
    details = {
        "eligible": s['eligibility']['eligible'],
        "max_loan": s['eligibility']['max_loan'],
        "policy_info": s['eligibility']['policy_info'],
        "cibil score": s['eligibility']['cibil score'],
        "dti": s['eligibility']['DTI'],
        "existing_debt": s['monthly_debt'],
        "income": s["income_annual"],
    }
    # context = f'income: {s["income_annual"]}, cibil_score: {s["cibil_score"]}, value: {s["asset_value"]}'
    res = decision_recommendation_agent(details, s["loan_type"])
    s["recommendation"] = res["recommendation"]
    s["policy_sources"] = res["policy_sources"]
    return s

# graph.add_node("customer_node", customer_node)
# graph.add_node("document_node", document_node)
graph.add_node("eligibility_node", eligibility_node)
graph.add_node("decision_node", decision_node)


graph.set_entry_point("eligibility_node")
# graph.add_edge("customer_node", "document_node")
# graph.add_edge("document_node", "eligibility_node")
graph.add_edge("eligibility_node", "decision_node")
graph.add_edge("decision_node", END)
workflow = graph.compile()

@app.post("/process_loan/")
async def process_loan(
        name: str = Form(...),
        loan_type: str = Form(...),  # home | personal | car
        monthly_debt: float = Form(...),
        cibil_report: UploadFile = File(...),
        salary_slips: List[UploadFile] = File(...),  # multiple
        property_doc: UploadFile = File(None),      # only for home
        car_doc: UploadFile = File(None)
    ):
    if loan_type not in ("home", "personal", "car"):
        raise HTTPException(status_code=400, detail="Invalid loan_type")

    if len(salary_slips) < 2:
        raise HTTPException(status_code=400, detail="At least 2 salary slip files are required")

    if loan_type == "home" and property_doc is None:
        raise HTTPException(status_code=400, detail="Property document required for home loan")

    if loan_type == "car" and car_doc is None:
        raise HTTPException(status_code=400, detail="Car document required for car loan")

    # Read file bytes
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
        asset_docs=asset_bytes,
        loan_type=loan_type
    )

    # Merge extracted values into state
    state = LoanState()
    state["loan_type"] = loan_type
    state["income_annual"] = doc_data["income_annual"]
    state["cibil_score"] = doc_data["cibil_score"]
    state["asset_value"] = doc_data["asset_value"]
    state['monthly_debt'] = monthly_debt

    # Run through eligibility and decision pipeline
    state = workflow.invoke(state)

    return {
        "customer_name": name,
        "eligibility": state["eligibility"],
        "recommendation": state["recommendation"],
        "policy_sources": state["policy_sources"]
    }


    s = LoanState()
    s["file_bytes"] = await file.read()
    s["filename"] = file.filename
    s["query"] = query
    # print("some idiot lang", s.keys())
    final = workflow.invoke(s)
    return {
        "customer_interaction": final["query"],
        "document_data": final["doc_data"],
        "eligibility": final["eligibility"],
        "policy_recommendation": final["recommendation"],
        "policy_sources": final["policy_sources"]
    }

@app.get("/")
def root():
    return {"message": "multi-agent home loan API running!"}
