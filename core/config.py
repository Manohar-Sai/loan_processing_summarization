import os
from dotenv import load_dotenv
load_dotenv(override=True)


# Gemini 2.0 API cofig
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# Pinecone config
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
