from source.function import read_file, text_splitter, download_openai_embeddings  # Corrected typo in import
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Retrieve Pinecone API key from environment variables
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')  # Use getenv for safe retrieval

# Load extracted data from the directory
extracted_data = read_file("data/")
# Split extracted data into text chunks
text_chunks = text_splitter(extracted_data)  # Corrected typo in function call
# Download embeddings from OpenAI
embeddings = download_openai_embeddings()

# Initialize Pinecone connection
pc = Pinecone(api_key=PINECONE_API_KEY)

# Define index parameters
index_name = "chatbot-index"
# Create Pinecone index with specified configuration
pc.create_index(
    name=index_name,
    dimension=3072, 
    metric="cosine", 
    spec=ServerlessSpec(
        cloud="gcp", 
        region="europe-west4"
    )
)

# Create a Pinecone vector store for document search
docsearch = PineconeVectorStore.from_documents(
    documents=text_chunks,
    index_name=index_name,
    embedding=embeddings
)
