import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.utils.file_utils import load_pdf_documents, split_documents
from src.core.embeddings import get_openai_embeddings
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from config.settings import Config

def setup_pinecone_index():
    """Setup Pinecone index with documents from data directory."""
    print("\n" + "="*70)
    print("🚀 CHATBOT IT SUPPORT UII - INDEX SETUP")
    print("="*70)
    
    # Validate configuration
    print("🔐 Validating configuration...")
    try:
        Config.validate()
        print("   ✅ API keys validated")
    except ValueError as e:
        print(f"   ❌ Configuration error: {e}")
        return
    
    # Load PDF documents from data directory
    print("\n📂 Loading PDF documents...")
    pdf_documents = load_pdf_documents("data/")
    
    if not pdf_documents:
        print("❌ No documents loaded. Please add PDF files to data/ directory.")
        return
    
    # Split documents into text chunks
    print("✂️  Splitting documents into chunks...")
    print(f"   📊 Chunk size: 500 characters")
    print(f"   🔄 Chunk overlap: 20 characters")
    
    document_chunks = split_documents(pdf_documents)
    
    print(f"   📝 Created {len(document_chunks)} text chunks")
    
    # Calculate statistics
    total_chars = sum(len(chunk.page_content) for chunk in document_chunks)
    avg_chunk_size = total_chars / len(document_chunks) if document_chunks else 0
    
    print(f"   💾 Total content: {total_chars:,} characters")
    print(f"   📏 Average chunk size: {avg_chunk_size:.0f} characters")
    
    # Get embeddings
    print("\n🤖 Initializing OpenAI embeddings...")
    try:
        openai_embeddings = get_openai_embeddings()
        print("   ✅ OpenAI embeddings ready")
    except Exception as e:
        print(f"   ❌ Failed to initialize embeddings: {e}")
        return
    
    # Initialize Pinecone client
    print(f"\n🌲 Setting up Pinecone index: {Config.PINECONE_INDEX_NAME}")
    try:
        pinecone_client = Pinecone(api_key=Config.PINECONE_API_KEY)
        print("   ✅ Pinecone client initialized")
        
        # Check if index exists
        existing_indexes = pinecone_client.list_indexes()
        index_names = [idx.name for idx in existing_indexes]
        
        if Config.PINECONE_INDEX_NAME in index_names:
            print(f"   ♻️  Index '{Config.PINECONE_INDEX_NAME}' already exists - will upsert documents")
        else:
            print(f"   🆕 Creating new index '{Config.PINECONE_INDEX_NAME}'")
            pinecone_client.create_index(
                name=Config.PINECONE_INDEX_NAME,
                dimension=3072,
                metric="cosine",
                spec=ServerlessSpec(cloud="gcp", region="europe-west4")
            )
            print("   ✅ Index created successfully")
            
    except Exception as e:
        print(f"   ❌ Pinecone setup failed: {e}")
        return
    
    # Create vector store from split documents
    print("\n🔮 Creating embeddings and upserting to vector store...")
    print(f"   📤 Processing {len(document_chunks)} chunks...")
    
    try:
        PineconeVectorStore.from_documents(
            documents=document_chunks,
            index_name=Config.PINECONE_INDEX_NAME,
            embedding=openai_embeddings
        )
        
        print("   ✅ Documents successfully embedded and stored")
        
    except Exception as e:
        print(f"   ❌ Vector store creation failed: {e}")
        return
    
    print("\n" + "="*70)
    print("🎉 INDEX SETUP COMPLETED SUCCESSFULLY")
    print("="*70)
    print(f"📊 Summary:")
    print(f"   📁 Files processed: {len(set(doc.metadata.get('file_name', 'unknown') for doc in pdf_documents))}")
    print(f"   📄 Documents loaded: {len(pdf_documents)}")
    print(f"   📝 Text chunks created: {len(document_chunks)}")
    print(f"   🌲 Pinecone index: {Config.PINECONE_INDEX_NAME}")
    print(f"   🎯 Status: READY FOR QUERIES")
    print("="*70 + "\n")

if __name__ == "__main__":
    setup_pinecone_index()