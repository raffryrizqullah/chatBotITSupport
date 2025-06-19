from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_pdf_documents(directory_path):
    """Load PDF documents from the specified directory."""
    pdf_loader = DirectoryLoader(directory_path, glob="*.pdf", loader_cls=PyPDFLoader)
    return pdf_loader.load()

def split_documents(documents, chunk_size=500, chunk_overlap=20):
    """Split documents into text chunks based on chunk size."""
    document_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap
    )
    return document_splitter.split_documents(documents)