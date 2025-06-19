from src.utils.file_utils import load_pdf_documents, split_documents
from src.core.embeddings import get_openai_embeddings
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from config.settings import Config

def setup_pinecone_index():
    """Setup Pinecone index with documents from data directory."""
    Config.validate()
    
    # Load PDF documents from data directory
    pdf_documents = load_pdf_documents("data/")
    
    # Split documents into text chunks
    document_chunks = split_documents(pdf_documents)
    
    # Get embeddings
    openai_embeddings = get_openai_embeddings()
    
    # Initialize Pinecone client
    pinecone_client = Pinecone(api_key=Config.PINECONE_API_KEY)
    
    # Create Pinecone index with specified specifications
    pinecone_client.create_index(
        name=Config.PINECONE_INDEX_NAME,
        dimension=3072,
        metric="cosine",
        spec=ServerlessSpec(cloud="gcp", region="europe-west4")
    )
    
    # Create vector store from split documents
    PineconeVectorStore.from_documents(
        documents=document_chunks,
        index_name=Config.PINECONE_INDEX_NAME,
        embedding=openai_embeddings
    )
    
    print(f"Successfully created and populated index: {Config.PINECONE_INDEX_NAME}")

if __name__ == "__main__":
    setup_pinecone_index()