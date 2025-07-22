# core/rag.py
import os
import pinecone
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.chains import RetrievalQA
from core.config import PINECONE_API_KEY, PINECONE_ENV, GOOGLE_API_KEY


pc = Pinecone(api_key=PINECONE_API_KEY)


index_name = os.getenv("PINECONE_INDEX", "loan-policy-index")
if not pc.list_indexes().names():
    print(PINECONE_ENV)
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV)
    )
index = pc.Index(index_name)

embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001", google_api_key=GOOGLE_API_KEY)
vector_store = PineconeVectorStore(index=index, embedding=embeddings, text_key="text")

# 5. Build RetrievalQA chain
# retrieval_qa = RetrievalQA.from_chain_type(
#     llm=None,  # Will be set per-call (agent uses Gemini chat)
#     chain_type="stuff",
#     retriever=vector_store.as_retriever(search_kwargs={"k": 4}),
#     return_source_documents=True
# ) not required here

def run_rag_query(llm, query: str):
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(search_kwargs={"k": 4}),
        return_source_documents=True
    )
    result = qa(query)
    return {
        "answer": result["result"],
        "sources": [
            {"text": doc.page_content, "metadata": doc.metadata}
            for doc in result["source_documents"]
        ]
    }
