# agents/document_agent.py

import mimetypes
from base64 import b64encode
from langchain_core.messages import HumanMessage
from core.llm import get_gemini_llm
from agents.schemas import DocumentExtraction

def encode_file(file_bytes: bytes, filename: str) -> dict:
    ext = filename.lower().split('.')[-1]
    mime = mimetypes.guess_type(filename)[0] #or "application/octet-stream"
    print(mime, 'idiot---------------------')
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
    loan_type: str,
) -> DocumentExtraction:
    llm = get_gemini_llm()

    parts = [
        {"type": "text", "text": (
            "Extract the following in JSON:\n"
            "- income_annual (annual income in INR): Calulate this based on attached payslips and calulate for annual\n"
            "- cibil_score (integer): Extract this from the attached cibil document\n"
            "- asset_value (property or car value in INR): Extract this from the attached asset docucmentLl"
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



# def document_processing_agent_multimodal(file_bytes: bytes, filename: str) -> dict:
#     ext = filename.lower().split('.')[-1]
#     mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
#     content_type = "image" if ext in ["jpg", "jpeg", "png"] else "file"
#     data_b64 = b64encode(file_bytes).decode()
#     # encoded = b64encode(file_bytes).decode("utf-8")
#     msg = HumanMessage(content=[
#         {"type": "text", "text": (
#             "You are a document extraction assistant for loan processing. "
#             "Extract the following fields in JSON, matching the schema: "
#             "loan_type (home, personal, or car), income (annual INR), "
#             "value (property/car/loan value in INR), existing_debt (monthly INR), "
#             "cibil_score (integer).\n\n"
#             "Return output as valid JSON conforming to the schema."
#         )},
#         {"type": content_type, "source_type": "base64", "mime_type": mime, "data": data_b64}
#     ])

#     structured = llm.with_structured_output(DocumentExtraction)
#     resp = structured.invoke([msg])
#     # resp is parsed Pydantic object
#     return resp.model_dump()