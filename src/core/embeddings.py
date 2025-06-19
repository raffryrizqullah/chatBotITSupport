from langchain_openai import OpenAIEmbeddings

def get_openai_embeddings():
    """Download OpenAI embeddings model with specified model."""
    return OpenAIEmbeddings(model="text-embedding-3-large")