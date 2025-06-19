from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
try:
    from unstructured.partition.pdf import partition_pdf
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False
    print("⚠ Unstructured not available, falling back to PyPDFLoader")
import os
import glob

def load_pdf_documents(directory_path):
    """Load PDF documents from the specified directory using unstructured or fallback to PyPDFLoader."""
    documents = []
    
    # Find all PDF files in directory
    pdf_files = glob.glob(os.path.join(directory_path, "*.pdf"))
    
    print("\n" + "="*70)
    print("📁 PDF DOCUMENT PROCESSING")
    print("="*70)
    
    if not pdf_files:
        print(f"ℹ️  No PDF files found in {directory_path}")
        return documents
    
    print(f"📊 Found {len(pdf_files)} PDF file(s) to process:")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"   {i}. {os.path.basename(pdf_file)}")
    
    print("\n" + "-"*70)
    
    for pdf_file in pdf_files:
        file_name = os.path.basename(pdf_file)
        print(f"\n🔄 Processing: {file_name}")
        print(f"   📍 Path: {pdf_file}")
        
        file_size = os.path.getsize(pdf_file) / 1024  # KB
        print(f"   📏 Size: {file_size:.1f} KB")
        
        # Try unstructured first if available
        if UNSTRUCTURED_AVAILABLE:
            try:
                elements = partition_pdf(
                    filename=pdf_file,
                    strategy="fast",  # Use "hi_res" for better quality but slower
                    extract_images_in_pdf=False,  # Keep simple for now
                    infer_table_structure=False,  # Keep simple for now
                    chunking_strategy="by_title",
                    max_characters=1500,
                    new_after_n_chars=1200,
                    combine_text_under_n_chars=100
                )
                
                # Convert elements to LangChain documents
                processed_elements = 0
                for element in elements:
                    if hasattr(element, 'text') and element.text.strip():
                        doc = Document(
                            page_content=element.text,
                            metadata={
                                "source": pdf_file,
                                "file_name": file_name,
                                "element_type": str(type(element).__name__),
                                "processor": "unstructured",
                                "char_count": len(element.text),
                                "element_id": f"elem_{processed_elements}"
                            }
                        )
                        documents.append(doc)
                        processed_elements += 1
                
                print(f"   ✅ Processed with unstructured")
                print(f"   📝 Elements extracted: {processed_elements}")
                print(f"   🎯 Status: SUCCESS")
                continue
                        
            except Exception as e:
                print(f"   ⚠️  Unstructured failed: {str(e)}")
                print(f"   🔄 Falling back to PyPDFLoader...")
        
        # Fallback to PyPDFLoader
        try:
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(pdf_file)
            fallback_docs = loader.load()
            
            # Add enhanced metadata
            for i, doc in enumerate(fallback_docs):
                doc.metadata.update({
                    "processor": "PyPDFLoader",
                    "file_name": file_name,
                    "char_count": len(doc.page_content),
                    "page_id": f"page_{i+1}"
                })
            
            documents.extend(fallback_docs)
            print(f"   ✅ Processed with PyPDFLoader")
            print(f"   📄 Pages extracted: {len(fallback_docs)}")
            print(f"   🎯 Status: SUCCESS")
            
        except Exception as fallback_error:
            print(f"   ❌ FAILED: Both processors failed")
            print(f"   🔍 Error: {str(fallback_error)}")
    
    print("\n" + "="*70)
    print("📊 PROCESSING SUMMARY")
    print("="*70)
    print(f"📁 Total files processed: {len(pdf_files)}")
    print(f"📄 Total documents extracted: {len(documents)}")
    
    # Document statistics
    if documents:
        processors = {}
        total_chars = 0
        for doc in documents:
            proc = doc.metadata.get('processor', 'unknown')
            processors[proc] = processors.get(proc, 0) + 1
            total_chars += doc.metadata.get('char_count', len(doc.page_content))
        
        print(f"💾 Total characters: {total_chars:,}")
        print(f"📊 Processor breakdown:")
        for proc, count in processors.items():
            print(f"   • {proc}: {count} documents")
    
    print("="*70 + "\n")
    return documents

def split_documents(documents, chunk_size=500, chunk_overlap=20):
    """Split documents into text chunks based on chunk size."""
    document_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap
    )
    return document_splitter.split_documents(documents)