# test_decision_agent.py
from core.llm import get_gemini_llm
from core.rag import run_rag_query
from agents.decision_agent import decision_recommendation_agent

def test_retrieval_and_recommendation():
    llm = get_gemini_llm()
    
    # Test case: Home loan scenario
    context = "income: 1200000, value: 5000000, cibil_score: 740"
    loan_type = "home"
    
    # Step 1: Test retrieval
    rag_res = run_rag_query(llm, query=f"{loan_type} loan policy context: {context}")
    assert rag_res["sources"], "No policy sources retrieved for home loan!"
    print("Retrieved sources for home loan:", [src["metadata"].get("loan_type") for src in rag_res["sources"]])
    
    # Step 2: Test summarization
    dec_res = decision_recommendation_agent(context, loan_type)
    print("🔹 Recommendation:", dec_res["recommendation"])
    assert "recommended_loan" in dec_res["recommendation"], "Recommendation missing key field!"
    
    # # Test case: Personal loan scenario
    # context2 = "income: 600000, value: 500000, cibil_score: 720"
    # loan_type2 = "personal"
    
    # rag_res2 = run_rag_query(llm, query=f"{loan_type2} loan policy context: {context2}")
    # assert rag_res2["sources"], "No policy sources retrieved for personal loan!"
    # print("✅ Retrieved sources for personal loan:", [src["metadata"].get("loan_type") for src in rag_res2["sources"]])
    
    # dec_res2 = decision_recommendation_agent(context2, loan_type2)
    # print("🔹 Recommendation:", dec_res2["recommendation"])

if __name__ == "__main__":
    test_retrieval_and_recommendation()
