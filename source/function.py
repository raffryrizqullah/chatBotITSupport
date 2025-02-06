from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings

def read_file(data):
    # Set up a PDF loader to raid directories for PDF files
    loader = DirectoryLoader(data, glob="*.pdf", loader_cls=PyPDFLoader)
    # Load and return the docs
    documents = loader.load()
    return documents

def text_splitter(extracted_data):
    # Initialize a splitter to hack texts into digestible pieces
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
    # Split and conquer the text data
    text_chunks = text_splitter.split_documents(extracted_data)
    return text_chunks

def download_openai_embeddings():
    # Grab the latest and greatest embeddings from OpenAI
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    return embeddings
