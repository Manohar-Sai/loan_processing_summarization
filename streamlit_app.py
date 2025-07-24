import streamlit as st
import requests
import tempfile
import pdfkit
from core.report_generator import generate_markdown_report

API_URL = "http://localhost:8000/process_loan/"

st.set_page_config(page_title="🏦 Loan Eligibility Checker", layout="wide")

st.title("🏦 Loan Application Assistant")

# 🔹 Two-column layout
left, right = st.columns([2, 1])

with left:
    st.subheader("📌 Applicant Information")

    name = st.text_input("Your Name")
    loan_type = st.selectbox("Loan Type", ["home", "personal", "car"])
    loan_amount = st.number_input("Required Loan Amount", min_value=0, step=1000)
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
    st.subheader("📜 Loan Report Preview")
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
            "req_loan_amount": loan_amount
        }

        response = requests.post(API_URL, data=data, files=files)

        if response.ok:
            result = response.json()
            decision = result["output"]

            # ✅ Generate Markdown Report
            md_report = generate_markdown_report(name, decision)
            preview_placeholder.markdown(md_report, unsafe_allow_html=True)

            # ✅ PDF Download
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
                {md_report.replace("\\n", "<br>")}
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
        else:
            st.error(f"❌ Error {response.status_code}: {response.text}")
