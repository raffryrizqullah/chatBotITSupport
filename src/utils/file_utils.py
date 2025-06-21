from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from typing import List, Dict, Any, Optional, Tuple
import os
import glob
import re

# Import PDF processing libraries with fallback handling
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False

try:
    from unstructured.partition.pdf import partition_pdf
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


class PDFStructureExtractor:
    """Extract structured content from PDFs using multiple processing libraries."""
    
    def __init__(self):
        self.available_processors = self._check_available_processors()
    
    def _check_available_processors(self) -> List[str]:
        """Check which PDF processors are available."""
        processors = []
        if PYMUPDF_AVAILABLE:
            processors.append("pymupdf")
        if PDFPLUMBER_AVAILABLE:
            processors.append("pdfplumber")
        if CAMELOT_AVAILABLE:
            processors.append("camelot")
        if UNSTRUCTURED_AVAILABLE:
            processors.append("unstructured")
        return processors
    
    def extract_with_pymupdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract structured content using PyMuPDF."""
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF not available")
        
        doc = fitz.open(pdf_path)
        extracted_data = {
            "text_blocks": [],
            "images": [],
            "links": [],
            "tables": [],
            "fonts": {},
            "metadata": {}
        }
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract text blocks with formatting
            blocks = page.get_text("dict")
            for block in blocks.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            font_info = {
                                "font": span.get("font", ""),
                                "size": span.get("size", 0),
                                "flags": span.get("flags", 0),
                                "color": span.get("color", 0)
                            }
                            
                            text_block = {
                                "text": span.get("text", ""),
                                "bbox": span.get("bbox", []),
                                "page": page_num + 1,
                                "font_info": font_info,
                                "is_header": self._is_header(font_info, span.get("text", ""))
                            }
                            extracted_data["text_blocks"].append(text_block)
                            
                            # Track fonts for analysis
                            font_key = f"{font_info['font']}_{font_info['size']}"
                            if font_key not in extracted_data["fonts"]:
                                extracted_data["fonts"][font_key] = {
                                    "count": 0,
                                    "font_info": font_info
                                }
                            extracted_data["fonts"][font_key]["count"] += 1
            
            # Extract images
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                extracted_data["images"].append({
                    "page": page_num + 1,
                    "index": img_index,
                    "bbox": page.get_image_bbox(img),
                    "description": f"Image {img_index + 1} on page {page_num + 1}"
                })
            
            # Extract links
            links = page.get_links()
            for link in links:
                extracted_data["links"].append({
                    "page": page_num + 1,
                    "bbox": link.get("from", []),
                    "uri": link.get("uri", ""),
                    "type": link.get("kind", "")
                })
        
        doc.close()
        return extracted_data
    
    def extract_with_pdfplumber(self, pdf_path: str) -> Dict[str, Any]:
        """Extract structured content using pdfplumber."""
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber not available")
        
        extracted_data = {
            "text": "",
            "tables": [],
            "chars": [],
            "metadata": {}
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract text
                page_text = page.extract_text()
                if page_text:
                    extracted_data["text"] += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                
                # Extract tables
                tables = page.extract_tables()
                for table_idx, table in enumerate(tables):
                    if table:
                        markdown_table = self._convert_table_to_markdown(table)
                        extracted_data["tables"].append({
                            "page": page_num + 1,
                            "index": table_idx,
                            "raw_table": table,
                            "markdown": markdown_table,
                            "bbox": page.bbox
                        })
                
                # Extract character-level information
                chars = page.chars
                extracted_data["chars"].extend([
                    {
                        **char,
                        "page": page_num + 1
                    } for char in chars
                ])
        
        return extracted_data
    
    def extract_with_camelot(self, pdf_path: str) -> Dict[str, Any]:
        """Extract tables using Camelot."""
        if not CAMELOT_AVAILABLE:
            raise ImportError("Camelot not available")
        
        try:
            # Extract tables using lattice method (better for tables with lines)
            tables_lattice = camelot.read_pdf(pdf_path, flavor='lattice', pages='all')
            
            # Fallback to stream method if lattice fails
            tables_stream = camelot.read_pdf(pdf_path, flavor='stream', pages='all')
            
            extracted_tables = []
            
            # Process lattice tables
            for table in tables_lattice:
                extracted_tables.append({
                    "method": "lattice",
                    "page": table.page,
                    "accuracy": table.accuracy,
                    "whitespace": table.whitespace,
                    "order": table.order,
                    "data": table.df.to_dict('records'),
                    "markdown": table.df.to_markdown(index=False)
                })
            
            # Process stream tables if lattice didn't find enough
            if len(tables_lattice) < 2:
                for table in tables_stream:
                    extracted_tables.append({
                        "method": "stream",
                        "page": table.page,
                        "accuracy": table.accuracy,
                        "whitespace": table.whitespace,
                        "order": table.order,
                        "data": table.df.to_dict('records'),
                        "markdown": table.df.to_markdown(index=False)
                    })
            
            return {"tables": extracted_tables}
            
        except Exception as e:
            return {"tables": [], "error": str(e)}
    
    def _is_header(self, font_info: Dict[str, Any], text: str) -> bool:
        """Determine if text is likely a header based on font properties."""
        if not text.strip():
            return False
        
        # Check font size (headers typically larger)
        if font_info.get("size", 0) > 14:
            return True
        
        # Check font flags (bold, italic indicators)
        flags = font_info.get("flags", 0)
        if flags & 2**4:  # Bold flag
            return True
        
        # Check text patterns (all caps, short lines)
        if len(text.strip()) < 100 and text.isupper():
            return True
        
        return False
    
    def _convert_table_to_markdown(self, table: List[List[str]]) -> str:
        """Convert table data to markdown format."""
        if not table or not table[0]:
            return ""
        
        markdown_rows = []
        
        # Header row
        header = "| " + " | ".join(str(cell) if cell else "" for cell in table[0]) + " |"
        markdown_rows.append(header)
        
        # Separator row
        separator = "| " + " | ".join("---" for _ in table[0]) + " |"
        markdown_rows.append(separator)
        
        # Data rows
        for row in table[1:]:
            if row:
                row_md = "| " + " | ".join(str(cell) if cell else "" for cell in row) + " |"
                markdown_rows.append(row_md)
        
        return "\n".join(markdown_rows)


class EnhancedPDFProcessor:
    """Process PDFs with multiple libraries and intelligent fallback."""
    
    def __init__(self):
        self.extractor = PDFStructureExtractor()
        self.processing_stats = {
            "total_processed": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "processors_used": {}
        }
    
    def process_pdf(self, pdf_path: str, use_enhanced: bool = True) -> List[Document]:
        """Process a PDF file with enhanced extraction capabilities."""
        file_name = os.path.basename(pdf_path)
        documents = []
        
        print(f"\n🔄 Enhanced processing: {file_name}")
        
        if not use_enhanced:
            return self._fallback_processing(pdf_path)
        
        # Try PyMuPDF first for structure extraction
        structure_data = None
        if PYMUPDF_AVAILABLE:
            try:
                print("   📖 Extracting structure with PyMuPDF...")
                structure_data = self.extractor.extract_with_pymupdf(pdf_path)
                self.processing_stats["processors_used"]["pymupdf"] = \
                    self.processing_stats["processors_used"].get("pymupdf", 0) + 1
                print(f"   ✅ Extracted {len(structure_data['text_blocks'])} text blocks")
            except Exception as e:
                error_msg = str(e)
                if "need item of full page image list" in error_msg:
                    print(f"   ⚠️  PyMuPDF skipped: Image-heavy PDF, using alternative processors")
                else:
                    print(f"   ⚠️  PyMuPDF failed: {error_msg}")
                print(f"   🔄 Continuing with other processors...")
        
        # Try pdfplumber for tables and text
        table_data = None
        if PDFPLUMBER_AVAILABLE:
            try:
                print("   📊 Extracting tables with pdfplumber...")
                table_data = self.extractor.extract_with_pdfplumber(pdf_path)
                self.processing_stats["processors_used"]["pdfplumber"] = \
                    self.processing_stats["processors_used"].get("pdfplumber", 0) + 1
                print(f"   ✅ Extracted {len(table_data['tables'])} tables")
            except Exception as e:
                print(f"   ⚠️  pdfplumber failed: {str(e)}")
        
        # Try Camelot for advanced table extraction
        camelot_data = None
        if CAMELOT_AVAILABLE and (not table_data or len(table_data.get("tables", [])) < 2):
            try:
                print("   🔍 Advanced table extraction with Camelot...")
                camelot_data = self.extractor.extract_with_camelot(pdf_path)
                self.processing_stats["processors_used"]["camelot"] = \
                    self.processing_stats["processors_used"].get("camelot", 0) + 1
                print(f"   ✅ Extracted {len(camelot_data['tables'])} tables")
            except Exception as e:
                print(f"   ⚠️  Camelot failed: {str(e)}")
        
        # Combine and structure the extracted data
        documents = self._combine_extracted_data(
            pdf_path, structure_data, table_data, camelot_data
        )
        
        # Fallback to unstructured if nothing worked
        if not documents:
            print("   🔄 Falling back to unstructured processing...")
            documents = self._fallback_processing(pdf_path)
        
        self.processing_stats["total_processed"] += 1
        if documents:
            self.processing_stats["successful_extractions"] += 1
        else:
            self.processing_stats["failed_extractions"] += 1
        
        return documents
    
    def _combine_extracted_data(
        self, 
        pdf_path: str, 
        structure_data: Optional[Dict[str, Any]], 
        table_data: Optional[Dict[str, Any]], 
        camelot_data: Optional[Dict[str, Any]]
    ) -> List[Document]:
        """Combine data from multiple extractors into structured documents."""
        documents = []
        file_name = os.path.basename(pdf_path)
        
        # Process structured text blocks
        if structure_data:
            structured_content = self._process_structured_content(
                structure_data, file_name, pdf_path
            )
            documents.extend(structured_content)
        
        # Process tables
        if table_data and table_data.get("tables"):
            table_docs = self._process_table_content(
                table_data["tables"], file_name, pdf_path, "pdfplumber"
            )
            documents.extend(table_docs)
        
        if camelot_data and camelot_data.get("tables"):
            camelot_docs = self._process_table_content(
                camelot_data["tables"], file_name, pdf_path, "camelot"
            )
            documents.extend(camelot_docs)
        
        # If we have pdfplumber text but no structure data, use it
        if not structure_data and table_data and table_data.get("text"):
            text_doc = Document(
                page_content=table_data["text"],
                metadata={
                    "source": pdf_path,
                    "file_name": file_name,
                    "processor": "pdfplumber_text",
                    "content_type": "full_text",
                    "char_count": len(table_data["text"])
                }
            )
            documents.append(text_doc)
        
        return documents
    
    def _process_structured_content(
        self, 
        structure_data: Dict[str, Any], 
        file_name: str, 
        pdf_path: str
    ) -> List[Document]:
        """Process structured content from PyMuPDF extraction."""
        documents = []
        
        # Group text blocks by page and structure
        pages_content = {}
        
        for block in structure_data["text_blocks"]:
            page_num = block["page"]
            if page_num not in pages_content:
                pages_content[page_num] = {
                    "headers": [],
                    "content": [],
                    "links": []
                }
            
            if block["is_header"]:
                pages_content[page_num]["headers"].append(block)
            else:
                pages_content[page_num]["content"].append(block)
        
        # Add links information
        for link in structure_data["links"]:
            page_num = link["page"]
            if page_num in pages_content:
                pages_content[page_num]["links"].append(link)
        
        # Create documents for each page
        for page_num, content in pages_content.items():
            # Build structured content
            page_text_parts = []
            
            # Add headers with markdown formatting
            for header in content["headers"]:
                header_text = header["text"].strip()
                if header_text:
                    # Determine header level based on font size
                    font_size = header["font_info"]["size"]
                    if font_size > 18:
                        header_level = "# "
                    elif font_size > 16:
                        header_level = "## "
                    elif font_size > 14:
                        header_level = "### "
                    else:
                        header_level = "#### "
                    
                    page_text_parts.append(f"{header_level}{header_text}")
            
            # Add regular content
            for text_block in content["content"]:
                text = text_block["text"].strip()
                if text:
                    page_text_parts.append(text)
            
            # Add links section if present
            if content["links"]:
                page_text_parts.append("\n## Links Found:")
                for link in content["links"]:
                    if link["uri"]:
                        page_text_parts.append(f"- [{link['uri']}]({link['uri']})")
            
            # Create document
            if page_text_parts:
                page_content = "\n\n".join(page_text_parts)
                
                doc = Document(
                    page_content=page_content,
                    metadata={
                        "source": pdf_path,
                        "file_name": file_name,
                        "page": page_num,
                        "processor": "pymupdf_structured",
                        "content_type": "structured_page",
                        "char_count": len(page_content),
                        "headers_count": len(content["headers"]),
                        "links_count": len(content["links"]),
                        "has_structure": True
                    }
                )
                documents.append(doc)
        
        return documents
    
    def _process_table_content(
        self, 
        tables: List[Dict[str, Any]], 
        file_name: str, 
        pdf_path: str, 
        processor: str
    ) -> List[Document]:
        """Process table content into documents."""
        documents = []
        
        for table_idx, table in enumerate(tables):
            table_content = table.get("markdown", "")
            
            if not table_content:
                continue
            
            # Enhance table with context
            table_parts = [f"## Table {table_idx + 1}"]
            
            if processor == "camelot":
                accuracy = table.get("accuracy", 0)
                table_parts.append(f"*Extraction accuracy: {accuracy:.1f}%*")
            
            table_parts.append(table_content)
            
            full_content = "\n\n".join(table_parts)
            
            doc = Document(
                page_content=full_content,
                metadata={
                    "source": pdf_path,
                    "file_name": file_name,
                    "page": table.get("page", 1),
                    "processor": f"{processor}_table",
                    "content_type": "table",
                    "table_index": table_idx,
                    "char_count": len(full_content),
                    "extraction_accuracy": table.get("accuracy", 0),
                    "is_table": True
                }
            )
            documents.append(doc)
        
        return documents
    
    def _fallback_processing(self, pdf_path: str) -> List[Document]:
        """Fallback processing using available simple methods."""
        documents = []
        file_name = os.path.basename(pdf_path)
        
        # Try unstructured first
        if UNSTRUCTURED_AVAILABLE:
            try:
                elements = partition_pdf(
                    filename=pdf_path,
                    strategy="fast",
                    extract_images_in_pdf=False,
                    infer_table_structure=True,
                    chunking_strategy="by_title",
                    max_characters=1500,
                    new_after_n_chars=1200,
                    combine_text_under_n_chars=100
                )
                
                for i, element in enumerate(elements):
                    if hasattr(element, 'text') and element.text.strip():
                        doc = Document(
                            page_content=element.text,
                            metadata={
                                "source": pdf_path,
                                "file_name": file_name,
                                "element_type": str(type(element).__name__),
                                "processor": "unstructured_fallback",
                                "char_count": len(element.text),
                                "element_id": f"elem_{i}"
                            }
                        )
                        documents.append(doc)
                
                return documents
                
            except Exception as e:
                print(f"   ⚠️  Unstructured fallback failed: {str(e)}")
        
        # Final fallback to PyPDFLoader
        try:
            from langchain_community.document_loaders import PyPDFLoader
            loader = PyPDFLoader(pdf_path)
            fallback_docs = loader.load()
            
            for i, doc in enumerate(fallback_docs):
                doc.metadata.update({
                    "processor": "pypdf_final_fallback",
                    "file_name": file_name,
                    "char_count": len(doc.page_content),
                    "page_id": f"page_{i+1}"
                })
            
            return fallback_docs
            
        except Exception as e:
            print(f"   ❌ Final fallback failed: {str(e)}")
            return []

def load_pdf_documents(directory_path, use_enhanced_processing=True):
    """
    Load PDF documents with enhanced processing capabilities.
    
    Args:
        directory_path: Directory containing PDF files
        use_enhanced_processing: Whether to use multi-library enhanced processing
    
    Returns:
        List of Document objects with extracted content and metadata
    """
    documents = []
    
    # Find all PDF files in directory
    pdf_files = glob.glob(os.path.join(directory_path, "*.pdf"))
    
    print("\n" + "="*80)
    print("📁 ENHANCED PDF DOCUMENT PROCESSING")
    print("="*80)
    
    if not pdf_files:
        print(f"ℹ️  No PDF files found in {directory_path}")
        return documents
    
    # Show available processors
    processor = EnhancedPDFProcessor()
    available_processors = processor.extractor.available_processors
    
    print(f"🔧 Available processors: {', '.join(available_processors)}")
    print(f"📊 Found {len(pdf_files)} PDF file(s) to process:")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"   {i}. {os.path.basename(pdf_file)}")
    
    print(f"\n🎛️  Processing mode: {'Enhanced' if use_enhanced_processing else 'Basic'}")
    print("=" * 80)
    
    # Process each PDF file
    for pdf_file in pdf_files:
        file_name = os.path.basename(pdf_file)
        file_size = os.path.getsize(pdf_file) / 1024  # KB
        
        print(f"\n📄 Processing: {file_name}")
        print(f"   📍 Path: {pdf_file}")
        print(f"   📏 Size: {file_size:.1f} KB")
        
        try:
            # Use enhanced processing or fallback
            if use_enhanced_processing:
                file_documents = processor.process_pdf(pdf_file, use_enhanced=True)
            else:
                file_documents = processor._fallback_processing(pdf_file)
            
            if file_documents:
                documents.extend(file_documents)
                print(f"   ✅ Successfully extracted {len(file_documents)} document chunks")
                
                # Show content type breakdown for this file
                content_types = {}
                for doc in file_documents:
                    content_type = doc.metadata.get('content_type', 'unknown')
                    content_types[content_type] = content_types.get(content_type, 0) + 1
                
                print(f"   📊 Content breakdown: {dict(content_types)}")
            else:
                print(f"   ❌ No content extracted from {file_name}")
                
        except Exception as e:
            print(f"   ❌ Processing failed: {str(e)}")
    
    # Generate comprehensive summary
    print("\n" + "="*80)
    print("📊 ENHANCED PROCESSING SUMMARY")
    print("="*80)
    
    print(f"📁 Total files processed: {len(pdf_files)}")
    print(f"📄 Total document chunks: {len(documents)}")
    
    if documents:
        # Processor statistics
        processors = {}
        content_types = {}
        total_chars = 0
        tables_found = 0
        structured_content = 0
        
        for doc in documents:
            # Processor breakdown
            proc = doc.metadata.get('processor', 'unknown')
            processors[proc] = processors.get(proc, 0) + 1
            
            # Content type breakdown
            content_type = doc.metadata.get('content_type', 'unknown')
            content_types[content_type] = content_types.get(content_type, 0) + 1
            
            # Statistics
            total_chars += doc.metadata.get('char_count', len(doc.page_content))
            if doc.metadata.get('is_table', False):
                tables_found += 1
            if doc.metadata.get('has_structure', False):
                structured_content += 1
        
        print(f"💾 Total characters: {total_chars:,}")
        print(f"📊 Processor breakdown:")
        for proc, count in processors.items():
            percentage = (count / len(documents)) * 100
            print(f"   • {proc}: {count} chunks ({percentage:.1f}%)")
        
        print(f"📋 Content type breakdown:")
        for content_type, count in content_types.items():
            percentage = (count / len(documents)) * 100
            print(f"   • {content_type}: {count} chunks ({percentage:.1f}%)")
        
        print(f"🔍 Enhanced features:")
        print(f"   📊 Tables extracted: {tables_found}")
        print(f"   🏗️  Structured content: {structured_content}")
        print(f"   🎯 Processing success rate: {(processor.processing_stats['successful_extractions'] / max(1, processor.processing_stats['total_processed'])) * 100:.1f}%")
    
    print("="*80 + "\n")
    return documents

def split_documents(documents, chunk_size=500, chunk_overlap=20):
    """Split documents into text chunks based on chunk size."""
    document_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap
    )
    return document_splitter.split_documents(documents)