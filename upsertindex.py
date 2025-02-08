from source.function import read_file, text_splitter, download_openai_embeddings
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os

load_dotenv()

# Ambil API key dari variabel lingkungan
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')

# Memuat dokumen PDF dari direktori data
pdf_documents = read_file("data/")

# Membagi dokumen ke dalam potongan-potongan teks
document_chunks = text_splitter(pdf_documents)

# Mengunduh embeddings dari OpenAI
openai_embeddings = download_openai_embeddings()

# Inisialisasi client Pinecone
pinecone_client = Pinecone(api_key=PINECONE_API_KEY)

# Membuat indeks Pinecone dengan spesifikasi yang ditentukan
pinecone_client.create_index(
    name="chatbot-index",
    dimension=3072,
    metric="cosine",
    spec=ServerlessSpec(cloud="gcp", region="europe-west4")
)

# Membuat vector store dari dokumen-dokumen yang telah di-split
pinecone_vector_store = PineconeVectorStore.from_documents(
    documents=document_chunks,
    index_name="chatbot-index",
    embedding=openai_embeddings
)
