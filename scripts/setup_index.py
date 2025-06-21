import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.utils.file_utils import load_pdf_documents, split_documents
from src.utils.chunking import enhanced_split_documents
from src.core.embeddings import get_openai_embeddings
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from config.settings import Config

def setup_pinecone_index(use_enhanced_processing=True, use_semantic_chunking=True):
    """
    Setup Pinecone index with enhanced PDF processing and semantic chunking.
    
    Args:
        use_enhanced_processing: Whether to use enhanced PDF extraction
        use_semantic_chunking: Whether to use semantic-aware chunking
    """
    print("\n" + "="*80)
    print("🚀 ENHANCED CHATBOT IT SUPPORT UII - INDEX SETUP")
    print("="*80)
    
    # Validate configuration
    print("🔐 Validating configuration...")
    try:
        Config.validate()
        print("   ✅ API keys validated")
    except ValueError as e:
        print(f"   ❌ Configuration error: {e}")
        return
    
    # Load PDF documents with enhanced processing
    print(f"\n📂 Loading PDF documents with {'enhanced' if use_enhanced_processing else 'basic'} processing...")
    pdf_documents = load_pdf_documents("data/", use_enhanced_processing=use_enhanced_processing)
    
    if not pdf_documents:
        print("❌ No documents loaded. Please add PDF files to data/ directory.")
        return
    
    # Choose chunking strategy
    if use_semantic_chunking:
        print("\n🧠 Processing with semantic-aware chunking...")
        document_chunks = enhanced_split_documents(
            pdf_documents, 
            enhance_metadata=True, 
            preserve_structure=True
        )
        chunking_method = "Semantic-aware chunking"
    else:
        print("\n✂️  Processing with basic text splitting...")
        print(f"   📊 Chunk size: 500 characters")
        print(f"   🔄 Chunk overlap: 20 characters")
        document_chunks = split_documents(pdf_documents)
        chunking_method = "Basic text splitting"
    
    if not document_chunks:
        print("❌ No chunks created from documents.")
        return
    
    # Enhanced statistics
    print(f"\n📊 CHUNKING ANALYSIS")
    print("="*60)
    print(f"📝 Total chunks created: {len(document_chunks)}")
    
    # Calculate comprehensive statistics
    total_chars = sum(len(chunk.page_content) for chunk in document_chunks)
    avg_chunk_size = total_chars / len(document_chunks) if document_chunks else 0
    
    print(f"💾 Total content: {total_chars:,} characters")
    print(f"📏 Average chunk size: {avg_chunk_size:.0f} characters")
    print(f"🎯 Chunking method: {chunking_method}")
    
    # Advanced statistics for semantic chunking
    if use_semantic_chunking:
        chunk_types = {}
        semantic_scores = []
        table_chunks = 0
        structured_chunks = 0
        
        for chunk in document_chunks:
            # Chunk type distribution
            chunk_type = chunk.metadata.get('chunk_type', 'unknown')
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            # Semantic scores
            semantic_score = chunk.metadata.get('semantic_score', 0)
            if semantic_score > 0:
                semantic_scores.append(semantic_score)
            
            # Special content counts
            if chunk.metadata.get('has_tables', False):
                table_chunks += 1
            if chunk.metadata.get('has_headers', False):
                structured_chunks += 1
        
        print(f"\n🔍 SEMANTIC ANALYSIS:")
        print(f"   📊 Table-containing chunks: {table_chunks}")
        print(f"   🏗️  Structured chunks: {structured_chunks}")
        
        if semantic_scores:
            avg_semantic_score = sum(semantic_scores) / len(semantic_scores)
            print(f"   🎯 Average semantic score: {avg_semantic_score:.3f}")
        
        print(f"   📋 Chunk type distribution:")
        for chunk_type, count in chunk_types.items():
            percentage = (count / len(document_chunks)) * 100
            print(f"      • {chunk_type}: {count} ({percentage:.1f}%)")
    
    # Get embeddings
    print("\n🤖 Initializing OpenAI embeddings...")
    try:
        openai_embeddings = get_openai_embeddings()
        print("   ✅ OpenAI embeddings ready")
    except Exception as e:
        print(f"   ❌ Failed to initialize embeddings: {e}")
        return
    
    # Initialize Pinecone client with enhanced setup
    print(f"\n🌲 Setting up Pinecone index: {Config.PINECONE_INDEX_NAME}")
    try:
        pinecone_client = Pinecone(api_key=Config.PINECONE_API_KEY)
        print("   ✅ Pinecone client initialized")
        
        # Check if index exists
        existing_indexes = pinecone_client.list_indexes()
        index_names = [idx.name for idx in existing_indexes]
        
        if Config.PINECONE_INDEX_NAME in index_names:
            print(f"   ♻️  Index '{Config.PINECONE_INDEX_NAME}' already exists - will upsert documents")
            
            # Get index stats
            index = pinecone_client.Index(Config.PINECONE_INDEX_NAME)
            stats = index.describe_index_stats()
            print(f"   📊 Current index stats: {stats.total_vector_count} vectors")
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
    
    # Batch processing for large document sets
    batch_size = 100  # Process in batches to avoid memory issues
    total_batches = (len(document_chunks) + batch_size - 1) // batch_size
    
    print(f"\n🔮 Creating embeddings and upserting to vector store...")
    print(f"   📤 Processing {len(document_chunks)} chunks in {total_batches} batch(es)")
    print(f"   🔄 Batch size: {batch_size} chunks per batch")
    
    try:
        if total_batches > 1:
            # Process in batches for large datasets
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min((batch_idx + 1) * batch_size, len(document_chunks))
                batch_chunks = document_chunks[start_idx:end_idx]
                
                print(f"   📦 Processing batch {batch_idx + 1}/{total_batches} ({len(batch_chunks)} chunks)...")
                
                PineconeVectorStore.from_documents(
                    documents=batch_chunks,
                    index_name=Config.PINECONE_INDEX_NAME,
                    embedding=openai_embeddings
                )
                
                print(f"   ✅ Batch {batch_idx + 1} completed")
        else:
            # Single batch processing
            PineconeVectorStore.from_documents(
                documents=document_chunks,
                index_name=Config.PINECONE_INDEX_NAME,
                embedding=openai_embeddings
            )
        
        print("   ✅ All documents successfully embedded and stored")
        
    except Exception as e:
        print(f"   ❌ Vector store creation failed: {e}")
        return
    
    # Verify index after processing
    print("\n🔍 Verifying index integrity...")
    try:
        index = pinecone_client.Index(Config.PINECONE_INDEX_NAME)
        final_stats = index.describe_index_stats()
        print(f"   ✅ Final index contains {final_stats.total_vector_count} vectors")
        
        # Test query to ensure index is working
        test_vector_store = PineconeVectorStore(
            index_name=Config.PINECONE_INDEX_NAME,
            embedding=openai_embeddings
        )
        test_vector_store.similarity_search("test", k=1)
        print(f"   🧪 Test query successful - index is operational")
        
    except Exception as e:
        print(f"   ⚠️  Index verification failed: {e}")
    
    # Final comprehensive summary
    print("\n" + "="*80)
    print("🎉 ENHANCED INDEX SETUP COMPLETED SUCCESSFULLY")
    print("="*80)
    
    # File and document statistics
    unique_files = len(set(doc.metadata.get('file_name', 'unknown') for doc in pdf_documents))
    
    print(f"📊 PROCESSING SUMMARY:")
    print(f"   📁 PDF files processed: {unique_files}")
    print(f"   📄 Raw documents extracted: {len(pdf_documents)}")
    print(f"   📝 Final chunks created: {len(document_chunks)}")
    print(f"   🎯 Processing mode: {'Enhanced' if use_enhanced_processing else 'Basic'}")
    print(f"   🧠 Chunking strategy: {chunking_method}")
    
    # Content quality metrics
    if use_semantic_chunking and semantic_scores:
        print(f"\n🎯 QUALITY METRICS:")
        print(f"   📊 Semantic coherence: {avg_semantic_score:.3f}/1.0")
        print(f"   🏗️  Structured content: {structured_chunks} chunks")
        print(f"   📋 Table content: {table_chunks} chunks")
    
    # Technical details
    print(f"\n🔧 TECHNICAL DETAILS:")
    print(f"   🌲 Pinecone index: {Config.PINECONE_INDEX_NAME}")
    print(f"   📡 Vector dimension: 3072")
    print(f"   🎯 Distance metric: cosine")
    print(f"   ☁️  Cloud: GCP (europe-west4)")
    
    print(f"\n✅ Status: READY FOR ENHANCED QUERIES")
    print("="*80 + "\n")
    
    return {
        "success": True,
        "files_processed": unique_files,
        "documents_extracted": len(pdf_documents),
        "chunks_created": len(document_chunks),
        "processing_mode": "enhanced" if use_enhanced_processing else "basic",
        "chunking_method": chunking_method,
        "semantic_score": avg_semantic_score if use_semantic_chunking and semantic_scores else None
    }

if __name__ == "__main__":
    setup_pinecone_index()