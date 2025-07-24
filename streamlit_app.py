# streamlit_app.py
import streamlit as st
import requests

API_URL = "http://localhost:8000/process_loan/"

st.title("🏦 Loan Application Assistant")

# 1. Loan type and dynamic guidance
name = st.text_input("Your Name")
loan_type = st.selectbox("Loan Type", ["home", "personal", "car"])
loan_amount = st.number_input("Required Loan Amount", min_value= 0, step = 1000)
monthly_debt = st.number_input("Monthly Debt Amount", min_value= 0, step = 1000)

if loan_type == "home":
    st.info("Please upload:\n• 2+ payslips (PDF)\n• CIBIL report (PDF)\n• Property document (PDF)")
elif loan_type == "personal":
    st.info("Please upload:\n• 2+ payslips (PDF)\n• CIBIL report (PDF)")
else:  # car
    st.info("Please upload:\n• 2+ payslips (PDF)\n• CIBIL report (PDF)\n• Car document (PDF)")

# File upload widgets
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

# 3. Submit
if st.button("Submit Application"):
    # Validations
    if not salary_slips or len(salary_slips) < 2:
        st.error("Please upload at least 2 payslips.")
    elif not cibil_report:
        st.error("CIBIL report is required.")
    elif loan_type == "home" and not property_doc:
        st.error("Property document is required for home loan.")
    elif loan_type == "car" and not car_doc:
        st.error("Car document is required for car loan.")
    else:
        files = []
        files.extend([("salary_slips", (sl.name, sl.getvalue(), sl.type)) for sl in salary_slips])
        files.append(("cibil_report", (cibil_report.name, cibil_report.getvalue(), cibil_report.type)))
        if property_doc:
            files.append(("property_doc", (property_doc.name, property_doc.getvalue(), property_doc.type)))
        if car_doc:
            files.append(("car_doc", (car_doc.name, car_doc.getvalue(), car_doc.type)))

        data = {"loan_type": loan_type,
                "name": name,
                "monthly_debt": monthly_debt}

        response = requests.post(API_URL, data=data, files=files)

        st.write("Status:", response.status_code)
        if response.ok:
            result = response.json()
            st.subheader("✅ Eligibility Check")
            st.json(result["eligibility"])
            st.subheader("💡 Recommendation & Policy Context")
            st.json(result["recommendation"])
            st.subheader("📚 Policy Sources")
            for src in result["policy_sources"]:
                loan_cat = src["metadata"].get("loan_type", "unknown").title()
                st.markdown(f"- **{loan_cat}**: {src['text'][:200]}…")
        else:
            st.error(f"Error {response.status_code}: {response.text}")
