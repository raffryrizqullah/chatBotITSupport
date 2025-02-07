from source.function import read_file, text_splitter, download_openai_embeddings
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os

load_dotenv()

PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')

extracted_data = read_file("data/")
text_chunks = text_splitter(extracted_data)
embeddings = download_openai_embeddings()

pc = Pinecone(api_key=PINECONE_API_KEY)

pc.create_index(
    name="chatbot-index",
    dimension=3072, 
    metric="cosine", 
    spec=ServerlessSpec(cloud="gcp", region="europe-west4")
)

docsearch = PineconeVectorStore.from_documents(
    documents=text_chunks,
    index_name="chatbot-index",
    embedding=embeddings
)
