from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

def read_file(directory_path):
    """Load PDF documents from the specified directory."""
    pdf_loader = DirectoryLoader(directory_path, glob="*.pdf", loader_cls=PyPDFLoader)
    documents = pdf_loader.load()
    return documents

def text_splitter(documents):
    """Split documents into text chunks based on chunk size."""
    document_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
    document_chunks = document_splitter.split_documents(documents)
    return document_chunks

def download_openai_embeddings():
    """Download OpenAI embeddings model with specified model."""
    openai_embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    return openai_embeddings

