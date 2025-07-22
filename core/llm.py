import os
from google import genai
from google.genai import types
from core.config import GOOGLE_API_KEY

from langchain_google_genai import ChatGoogleGenerativeAI
from core.config import GOOGLE_API_KEY

client = genai.Client()

def gemini_chat_prompt(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt],
        config=types.GenerateContentConfig(response_mime_type="text/plain")
    )
    return response.text

def gemini_image_extract(image_binary: bytes, instruction: str) -> str:
    part = types.Part.from_bytes(data=image_binary, mime_type="image/jpeg")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[instruction, part],
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    return response.text

def get_gemini_llm(model_name="gemini-2.0-flash", **kwargs):
    """
    Returns a Gemini LLM instance for chat and multimodal use.
    """
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=GOOGLE_API_KEY,
        temperature=0,
        **kwargs
    )

