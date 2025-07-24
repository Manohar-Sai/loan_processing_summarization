import mimetypes
from base64 import b64encode
from langchain_core.messages import HumanMessage
from core.llm import get_gemini_llm
from agents.schemas import DocumentExtraction

def encode_file(file_bytes: bytes, filename: str) -> dict:
    ext = filename.lower().split('.')[-1]
    mime = mimetypes.guess_type(filename)[0]
    content_type = "image" if ext in ["jpg", "jpeg", "png"] else "file"
    data_b64 = b64encode(file_bytes).decode()
    return {
        "type": content_type,
        "source_type": "base64",
        "mime_type": mime,
        "data": data_b64
    }

def document_processing_agent(
    salary_slips: dict,
    cibil_pdf: dict,
    asset_docs: dict,
) -> DocumentExtraction:
    
    llm = get_gemini_llm()

    parts = [
        {"type": "text", "text": (
            "Extract the following in JSON:\n"
            "- income_monthly (montly income in INR): Extract this based on attached payslips\n"
            "- cibil_score (integer): Extract this from the attached cibil document\n"
            "- asset_value (property or car value in INR): Extract this from the attached asset docucment\n"
            "Instructions\n"
            "- Always ignore special characters in output"

            
        )}
    ]

    # Add all document parts
    for slip_name, slip in salary_slips.items():
        parts.append(encode_file(slip, slip_name))
    for cibil_name, cibil in cibil_pdf.items():
         parts.append(encode_file(cibil, cibil_name))
    for doc_name, doc in asset_docs.items():
        parts.append(encode_file(doc, doc_name))

    structured = llm.with_structured_output(DocumentExtraction)
    resp = structured.invoke([HumanMessage(content=parts)])
    return resp.model_dump()
