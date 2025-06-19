from source.function import read_file, text_splitter, download_openai_embeddings
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os

load_dotenv()

# Get API key from environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# Load PDF documents from data directory
pdf_documents = read_file("data/")

# Split documents into text chunks
document_chunks = text_splitter(pdf_documents)

# Download embeddings from OpenAI
openai_embeddings = download_openai_embeddings()

# Initialize Pinecone client
pinecone_client = Pinecone(api_key=PINECONE_API_KEY)

# Create Pinecone index with specified specifications
pinecone_client.create_index(
    name="chatbot-index",
    dimension=3072,
    metric="cosine",
    spec=ServerlessSpec(cloud="gcp", region="europe-west4")
)

# Create vector store from split documents
pinecone_vector_store = PineconeVectorStore.from_documents(
    documents=document_chunks,
    index_name="chatbot-index",
    embedding=openai_embeddings
)

