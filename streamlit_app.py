import streamlit as st
import tempfile
import pdfkit
import markdown
from core.report_generator import generate_markdown_report
from langgraph.graph import StateGraph, END
from agents.customer_agent import customer_interaction_agent
from agents.document_agent import document_processing_agent
from agents.eligibility_agent import eligibility_risk_assessment_agent
from agents.decision_agent import decision_recommendation_agent
from typing import TypedDict, Any, List

import re

def remove_emojis(text: str) -> str:
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002700-\U000027BF"  # other symbols
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U00002600-\U000026FF"  # misc symbols
        "\U00002B00-\U00002BFF"  # arrows
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

def fix_encoding(text: str) -> str:
    try:
        return text.encode('latin1').decode('utf-8')
    except:
        return text

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

# Initialize the workflow graph
graph = StateGraph(LoanState)

def eligibility_node(s: LoanState):
    applicant = {
        "loan_type": s["loan_type"],
        "income_monthly": s["income_monthly"],
        "cibil_score": s["cibil_score"],
        "monthly_debt": s["monthly_debt"],
    }
    if s['loan_type'] != 'personal':
        applicant |= {"asset_value": s["asset_value"]}
    result = eligibility_risk_assessment_agent(applicant)
    for key, value in result.items():
        s[key] = value
    return s

def decision_node(s: LoanState):
    res = decision_recommendation_agent(s)
    for key, value in res.items():
        s[key] = value
    return s

# Create graph nodes and edges
graph.add_node("eligibility_node", eligibility_node)
graph.add_node("decision_node", decision_node)
graph.set_entry_point("eligibility_node")
graph.add_edge("eligibility_node", "decision_node")
graph.add_edge("decision_node", END)
workflow = graph.compile()

def process_loan(
    name: str,
    loan_type: str,
    monthly_debt: float,
    cibil_report,
    salary_slips,
    property_doc=None,
    car_doc=None
):
    # Input validation
    if loan_type not in ("home", "personal", "car"):
        st.error("Invalid loan type")
        return None
    if not salary_slips or len(salary_slips) < 1:
        st.error("At least 1 salary slip file is required")
        return None
    if loan_type == "home" and not property_doc:
        st.error("Property document required for home loan")
        return None
    if loan_type == "car" and not car_doc:
        st.error("Car document required for car loan")
        return None

    # Prepare document bytes
    salary_bytes = {slip.name: slip.getvalue() for slip in salary_slips}
    cibil_bytes = {cibil_report.name: cibil_report.getvalue()}
    asset_bytes = {}
    if loan_type == "home" and property_doc:
        asset_bytes = {property_doc.name: property_doc.getvalue()}
    elif loan_type == "car" and car_doc:
        asset_bytes = {car_doc.name: car_doc.getvalue()}

    # Process documents
    doc_data = document_processing_agent(
        salary_slips=salary_bytes,
        cibil_pdf=cibil_bytes,
        asset_docs=asset_bytes
    )

    # Initialize and process loan state
    state = LoanState()
    state["name"] = name
    state["loan_type"] = loan_type
    state["income_monthly"] = doc_data["income_monthly"]
    state["cibil_score"] = doc_data["cibil_score"]
    state["asset_value"] = doc_data["asset_value"]
    state['monthly_debt'] = monthly_debt

    state = workflow.invoke(state)
    return {"output": state}

# Streamlit UI
st.set_page_config(page_title="🏦 Loan Eligibility Checker", layout="wide")
st.title("🏦 Loan Application Assistant")

# Two-column layout
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
        type=["pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=True
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
    preview_placeholder = st.empty()

# Submit action
if submitted:
    result = process_loan(
        name=name,
        loan_type=loan_type,
        monthly_debt=monthly_debt,
        cibil_report=cibil_report,
        salary_slips=salary_slips,
        property_doc=property_doc,
        car_doc=car_doc
    )

    if result:
        decision = result["output"]
        md_report = generate_markdown_report(name, decision)
        preview_placeholder.markdown(md_report, unsafe_allow_html=True)

        # Generate PDF
        html_body = markdown.markdown(md_report)
        html_report = fix_encoding(remove_emojis(f"""
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
        """))

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdfkit.from_string(html_report, tmp_pdf.name)
            with open(tmp_pdf.name, "rb") as pdf_file:
                st.download_button(
                    label="📥 Download Loan Approval Report (PDF)",
                    data=pdf_file,
                    file_name=f"{name}_loan_report.pdf",
                    mime="application/pdf"
                )

        st.json(decision)