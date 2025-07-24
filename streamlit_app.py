import streamlit as st
import requests
import tempfile
import pdfkit
from core.report_generator import generate_markdown_report
import markdown

# API_URL = "http://localhost:8000/process_loan/"


from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from langgraph.graph import StateGraph, END
from agents.customer_agent import customer_interaction_agent
from agents.document_agent import document_processing_agent
from agents.eligibility_agent import eligibility_risk_assessment_agent
from agents.decision_agent import decision_recommendation_agent
from fastapi.middleware.cors import CORSMiddleware
from typing import TypedDict, Any, List


# app = FastAPI(title="Gemini Loan Processor")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:8501"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

class LoanState(TypedDict):
    name: str
    loan_type: str
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


# # app
# # @app.post("/process_loan/")
def process_loan(
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
    salary_bytes = {slip.name: slip.getvalue() for slip in salary_slips}
    cibil_bytes = {cibil_report.name: cibil_report.getvalue()}
    asset_bytes = {}
    if loan_type == "home" and property_doc:
        asset_bytes = {property_doc.name: property_doc.getvalue()}
    elif loan_type == "car" and car_doc:
        asset_bytes = {car_doc.name: car_doc.getvalue()}
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

    state = workflow.invoke(state)

    return {
        # "customer_name": name,
        # "eligibility": state["eligibility"],
        # "recommendation": state["recommendation"],
        # # "policy_sources": state["policy_sources"]
        "output": state
    }

# # @app.get("/")
# def root():
#     return {"message": "multi-agent home loan API running!"}


# def hello(name):
#     return "dummy ga"




st.set_page_config(page_title="🏦 Loan Eligibility Checker", layout="wide")

st.title("🏦 Loan Application Assistant")

# 🔹 Two-column layout
left, right = st.columns([2, 1])

with left:
    st.subheader("📌 Applicant Information")

    name = st.text_input("Your Name")
    loan_type = st.selectbox("Loan Type", ["home", "personal", "car"])
    monthly_debt = st.number_input("Monthly Debt Amount", min_value=0, step=1000)

    if loan_type == "home":
        st.info("Please upload:\n✅ 1+ payslips (PDF/JPG/PNG)\n✅ CIBIL report (PDF)\n✅ Property document (PDF)")
    elif loan_type == "personal":
        st.info("Please upload:\n✅ 1+ payslips (PDF/JPG/PNG)\n✅ CIBIL report (PDF)")
    else:  # car
        st.info("Please upload:\n✅ 1+ payslips (PDF/JPG/PNG)\n✅ CIBIL report (PDF)\n✅ Car document (PDF)")

    salary_slips = st.file_uploader(
        "Salary Slips (PDF/JPG/PNG, multiple)",
        type=["pdf", "jpg", "jpeg", "png"], accept_multiple_files=True
    )
    cibil_report = st.file_uploader(
        "CIBIL Report (PDF/JPG/PNG)",
        type=["pdf", "jpg", "jpeg", "png"]
    )
    property_doc = st.file_uploader(
        "Property Document (PDF/JPG/PNG)",
        type=["pdf", "jpg", "jpeg", "png"]
    ) if loan_type == "home" else None
    car_doc = st.file_uploader(
        "Car Document (PDF/JPG/PNG)",
        type=["pdf", "jpg", "jpeg", "png"]
    ) if loan_type == "car" else None

    submitted = st.button("🚀 Submit Application")

with right:
    # st.subheader("📜 Loan Report Preview")
    preview_placeholder = st.empty()

# 🔹 Submit Action
if submitted:
    if not salary_slips or len(salary_slips) < 1:
        st.error("⚠️ Please upload at least 1 payslip.")
    elif not cibil_report:
        st.error("⚠️ CIBIL report is required.")
    elif loan_type == "home" and not property_doc:
        st.error("⚠️ Property document is required for home loan.")
    elif loan_type == "car" and not car_doc:
        st.error("⚠️ Car document is required for car loan.")
    else:
        files = []
        files.extend([("salary_slips", (sl.name, sl.getvalue(), sl.type)) for sl in salary_slips])
        files.append(("cibil_report", (cibil_report.name, cibil_report.getvalue(), cibil_report.type)))
        if property_doc:
            files.append(("property_doc", (property_doc.name, property_doc.getvalue(), property_doc.type)))
        if car_doc:
            files.append(("car_doc", (car_doc.name, car_doc.getvalue(), car_doc.type)))

        data = {
            "loan_type": loan_type,
            "name": name,
            "monthly_debt": monthly_debt,
        }
        # st.markdown(hello('this is working'))

        # response = requests.post(API_URL, data=data, files=files)
        result = process_loan(
            name,
            loan_type,
            monthly_debt,
            cibil_report,
            salary_slips,
            property_doc,
            car_doc         
        )

        # if response.ok:
        #     result = response.json()
        decision = result["output"]

        # ✅ Generate Markdown Report
        md_report = generate_markdown_report(name, decision)
        preview_placeholder.markdown(md_report, unsafe_allow_html=True)

        # ✅ PDF Download
        html_body = markdown.markdown(md_report)
        html_report = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                h1 {{ color: #0B5394; }}
                h2 {{ color: #1C4587; border-bottom:1px solid #ccc; padding-bottom:4px; }}
            </style>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """
        st.json(decision)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdfkit.from_string(html_report, tmp_pdf.name)
            with open(tmp_pdf.name, "rb") as pdf_file:
                st.download_button(
                    label="📥 Download Loan Approval Report (PDF)",
                    data=pdf_file,
                    file_name=f"{name}_loan_report.pdf",
                    mime="application/pdf"
                )
        # else:
        #     st.error(f"❌ Error {response.status_code}: {response.text}")
