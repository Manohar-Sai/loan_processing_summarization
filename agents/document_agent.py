from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from core.config import GOOGLE_API_KEY
import json

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0
)

def document_processing_agent_multimodal(image_binary: bytes) -> dict:
    """
    Sends the image + prompt to Gemini and parses returned JSON.
    """
    # Encode to base64 inline format
    from base64 import b64encode
    encoded = b64encode(image_binary).decode("utf-8")
    
    msg = HumanMessage(content=[
        {
            "type": "text",
            "text": "Extract the following fields in JSON: income, property_value, cibil_score."
        },
        {
            "type": "image",
            "source_type": "base64",
            "mime_type": "image/jpeg",
            "data": encoded
        }
    ])
    
    response = llm.invoke([msg])
    # Expecting JSON text
    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON from Gemini: {response.content}")
