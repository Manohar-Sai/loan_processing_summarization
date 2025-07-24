from pinecone import Pinecone, ServerlessSpec
import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from core.config import PINECONE_API_KEY, PINECONE_ENV, GOOGLE_API_KEY

pc = Pinecone(api_key=PINECONE_API_KEY)


# load documents from given folder
def load_documents_from_folder(folder_path: str):
    docs = []
    for fname in os.listdir(folder_path):
        full = os.path.join(folder_path, fname)
        if fname.lower().endswith(".pdf"):
            loader = PyPDFLoader(full)
        elif fname.lower().endswith((".txt", ".md")):
            loader = TextLoader(full)
        else:
            continue
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

        chunks = splitter.split_documents(loader.load())

        # ✅ Inject loan_type metadata based on filename (home_loan_policy.txt → "home")
        loan_type = Path(fname).stem.split("_")[0]
        for c in chunks:
            c.metadata["loan_type"] = loan_type
            c.metadata["source_file"] = fname.split('/')[-1]
        docs.extend(chunks)
    return docs

index_name = os.getenv("PINECONE_INDEX", "loan-policy-index")
if not pc.list_indexes().names():
    print(PINECONE_ENV)
    pc.create_index(
        name=index_name,
        dimension=3072,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV)
    )
index = pc.Index(index_name)

embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001", google_api_key=GOOGLE_API_KEY)
vector_store = PineconeVectorStore(index=index, embedding=embeddings, text_key="text")

docs = load_documents_from_folder("policies/")
vector_store.add_documents(docs)

print(f"Ingested {len(docs)} document chunks into index '{index_name}'.")