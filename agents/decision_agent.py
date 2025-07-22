from core.llm import client, types, get_gemini_llm
from core.rag import run_rag_query

def decision_recommendation_agent(context: str) -> dict:
    """
    Given a structured context (e.g. "income: 80000, property: 5000000"),
    this agent fetches relevant loan policy guidance from Pinecone and
    formulates a recommendation using Gemini.
    Returns: {
        "answer": str,
        "sources": [ {text, metadata}, ... ]
    }
    """

    llm =get_gemini_llm()
    rag_result = run_rag_query(llm=llm, query=context)
    policy_text = rag_result["answer"]
    sources = rag_result["sources"]

    prompt = (
        f"Based on the following extracted loan details:\n"
        f"{context}\n\n"
        f"And referring to these policy snippets:\n{policy_text}\n\n"
        "Please summarize whether the loan is advisable, outline key conditions, "
        "and suggest next steps in JSON with fields: summary, conditions, next_steps."
    )

    gemini_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt],
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    recommendation = gemini_response.text

    return {
        "recommendation": recommendation,
        "policy_sources": sources
    }
