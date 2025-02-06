from source.function import read_file, text_splitter, download_openai_embeddings
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os

load_dotenv()  # Load .env file

PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')  # API key retrieval

extracted_data = read_file("data/")  # Load data from directory
text_chunks = text_splitter(extracted_data)  # Split data into chunks
embeddings = download_openai_embeddings()  # Get embeddings from OpenAI

pc = Pinecone(api_key=PINECONE_API_KEY)  # Initialize Pinecone

# Create Pinecone index with specified configurations
pc.create_index(
    name="chatbot-index",
    dimension=3072, 
    metric="cosine", 
    spec=ServerlessSpec(cloud="gcp", region="europe-west4")
)

# Initialize a Pinecone vector store with documents
docsearch = PineconeVectorStore.from_documents(
    documents=text_chunks,
    index_name="chatbot-index",
    embedding=embeddings
)
