from fastapi import FastAPI, UploadFile, File
from langgraph.graph import StateGraph, END
from agents.customer_agent import customer_interaction_agent
from agents.document_agent import document_processing_agent_multimodal
from agents.eligibility_agent import eligibility_risk_assessment_agent
from agents.decision_agent import decision_recommendation_agent
import json

app = FastAPI()

class LoanState:
    query: str = ""
    doc_data: dict = {}
    eligibility: dict = {}
    recommendation: str = ""

graph = StateGraph(LoanState)

# @graph.node
def customer_node(s: LoanState):
    s.query = customer_interaction_agent(s.query)
    return s

# @graph.node
def document_node(s: LoanState):
    s.doc_data = document_processing_agent_multimodal(s.image_binary)
    return s

# @graph.node
def eligibility_node(s: LoanState):
    s.eligibility = eligibility_risk_assessment_agent(s.doc_data)
    return s

# @graph.node
def decision_node(s: LoanState):
    context = f"income: {s.doc_data['income']}, property: {s.doc_data['property_value']}"
    result = decision_recommendation_agent(context)
    s.recommendation = result["recommendation"]
    s.policy_sources = result["policy_sources"]
    return s

graph.add_node("customer_node", customer_node)
graph.add_node("document_node", document_node)
graph.add_node("eligibility_node", eligibility_node)
graph.add_node("decision_node", decision_node)


graph.add_edge("customer_node", "document_node")
graph.add_edge("document_node", "eligibility_node")
graph.add_edge("eligibility_node", "decision_node")
graph.set_entry_point("customer_node")
graph.add_edge("decision_node", END)
workflow = graph.compile()

@app.post("/process_loan_multimodal_gemini2/")
async def process_loan(query: str, file: UploadFile = File(...)):
    img = await file.read()
    state = LoanState()
    state.query = query
    state.image_binary = img
    final = workflow.invoke(state)
    return {
        "customer_interaction": final.query,
        "document_data": final.doc_data,
        "eligibility": final.eligibility,
        "policy_recommendation": final.recommendation
    }

@app.get("/")
def root():
    return {"message": "multi-agent home loan API running!"}
