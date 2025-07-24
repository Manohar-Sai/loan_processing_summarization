import os
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from core.llm import get_gemini_embedder
from core.config import PINECONE_API_KEY, PINECONE_ENV

pc = Pinecone(api_key=PINECONE_API_KEY)
INDEX_NAME = os.getenv("PINECONE_INDEX", "loan-policy-index")
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(name=INDEX_NAME, dimension=3072, metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV))
index = pc.Index(INDEX_NAME)

embeddings = get_gemini_embedder()
vector_store = PineconeVectorStore(index=index, embedding=embeddings, text_key="text")

def run_rag_query(llm, query: str):
    qa = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff",
        retriever=vector_store.as_retriever(search_kwargs={"k": 4}),
        return_source_documents=True
    )
    res = qa.invoke({"query": query})
    return {
        "answer": res["result"],
        "sources": [{"text": d.page_content, "metadata": d.metadata} for d in res["source_documents"]]
    }
