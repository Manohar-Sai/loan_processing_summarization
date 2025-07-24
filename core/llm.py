from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from core.config import GOOGLE_API_KEY
import asyncio
import threading

# Ensure an event loop exists in the current thread
def ensure_event_loop():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

def get_gemini_llm(model="gemini-2.0-flash", **kwargs):
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=GOOGLE_API_KEY,
        temperature=0,
        **kwargs
    )

def get_gemini_embedder():
    ensure_event_loop()
    return GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        google_api_key=GOOGLE_API_KEY,
        task_type="RETRIEVAL_DOCUMENT",
    )
