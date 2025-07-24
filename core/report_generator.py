def generate_markdown_report(applicant_name: str, decision: dict) -> str:
    """
    Generates a customer-friendly markdown loan approval report.
    """

    md = f"""
# 🏦 Loan Report

**Applicant:** {applicant_name}  
**Loan Type:** {decision.get('loan_type', 'N/A')}  
**Summary:** {decision.get('summary', '')}  

---

"""
    if not decision['eligible']:
        md += """## ❌ Loan Rejection Details

        """
        for reason in decision.get("reasons", []):
            md += f"- {reason}\n"
    else:
        md += f"""
## ✅ Loan Details

- **Recommended Loan Amount:** ₹{decision.get('recommended_loan', 0):,.2f}  
- **Tenure:** {decision["policy_info"]["max_tenure"]} months  
- **Interest Rate:** {decision.get('applicable_rules', [])[0] if decision.get('applicable_rules') else 'N/A'}  
- **Recommended EMI:** ₹{decision.get('recommended_emi', 0):,.2f}
"""
        if "updated_DTI" in decision.keys():
             md += f"""- **DTI (Debt-to-Income):** {decision.get('updated_DTI', 0):.2f}%

---

"""
        else:
             md += f"""- **DTI (Debt-to-Income):** {decision.get('dti_percent', 0):.2f}%  

---

"""
    md += """
## 📜 Policy Rules Considered

"""
    for rule in decision.get("applicable_rules", []):
        md += f"- {rule}\n"
    if decision['eligible']:
        md += "\n---\n## 📝 Next Steps\n"
        for step in decision.get("next_steps", []):
            md += f"- {step}\n"
    else:
        md += """\n---\n## 📝 Recommendation
        
        """
        md += f"{decision.get("recommendation",[])}"
    md += "\n---\n**This report is system-generated based on current loan policies.**"
    return md