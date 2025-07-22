from langchain_google_genai import ChatGoogleGenerativeAI
from core.config import GOOGLE_API_KEY

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0
)

def customer_interaction_agent(user_query: str) -> str:
    """
    Prompts Gemini to clarify loan intent and collect key info:
    income, desired loan amount, property location/type, any existing debt.
    Returns Gemini's structured text response.
    """
    messages = [
        (
            "system",
            "You are a home‑loan assistant. Ask the user to provide income, desired loan amount, "
            "property value & location, and existing debts if any."
        ),
        ("human", user_query)
    ]
    response = llm.invoke(messages)
    return response.content
