from langchain_pinecone import PineconeVectorStore
from config.settings import Config

def get_vector_store(embeddings):
    """Initialize vector store from existing index."""
    return PineconeVectorStore.from_existing_index(
        index_name=Config.PINECONE_INDEX_NAME, 
        embedding=embeddings
    )

def get_retriever(vector_store, k=2):
    """Create retriever to search documents by similarity."""
    return vector_store.as_retriever(
        search_type="similarity", 
        search_kwargs={"k": k}
    )