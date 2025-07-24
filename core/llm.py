from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from core.config import GOOGLE_API_KEY

def get_gemini_llm(model="gemini-2.0-flash", **kwargs):
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=GOOGLE_API_KEY,
        temperature=0,
        **kwargs
    )

def get_gemini_embedder():
    return GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        google_api_key=GOOGLE_API_KEY,
        task_type="RETRIEVAL_DOCUMENT",
    )
