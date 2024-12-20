from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings

# Function to extract data from PDF files located in a directory
def read_file(data):
    # Initialize loader for directory with PDF files
    loader = DirectoryLoader(data, glob="*.pdf", loader_cls=PyPDFLoader)
    # Load documents from directory
    documents = loader.load()
    return documents

# Function to split extracted data into manageable text chunks
def text_splitter(extracted_data):
    # Define text splitter with specific chunk size and overlap
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
    # Split documents into chunks
    text_chunks = text_splitter.split_documents(extracted_data)
    return text_chunks

# Function to load embeddings from OpenAI
def download_openai_embeddings():
    # Initialize embeddings with specified model
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    return embeddings
