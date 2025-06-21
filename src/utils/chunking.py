"""
Advanced semantic-aware document chunking for enhanced PDF processing.

This module provides intelligent document splitting that preserves semantic structure,
tables, headers, and other document elements for improved search quality.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from langchain.schema.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class ChunkType(Enum):
    """Types of content chunks for classification."""
    NARRATIVE_TEXT = "narrative_text"
    TABLE_HEAVY = "table_heavy"
    LIST_HEAVY = "list_heavy"
    HEADER_SECTION = "header_section"
    CODE_BLOCK = "code_block"
    MIXED_CONTENT = "mixed_content"


class ContentClassifier:
    """Classifies document content to determine optimal chunking strategy."""
    
    @staticmethod
    def classify_content(text: str) -> ChunkType:
        """Classify text content to determine chunk type."""
        text_lower = text.lower()
        
        # Count various content indicators
        table_indicators = len(re.findall(r'\|.*\|', text)) + text.count('\t')
        list_indicators = len(re.findall(r'^\s*[-*•]\s', text, re.MULTILINE))
        numbered_list = len(re.findall(r'^\s*\d+\.\s', text, re.MULTILINE))
        header_indicators = len(re.findall(r'^#{1,6}\s', text, re.MULTILINE))
        code_indicators = text.count('```') + text.count('def ') + text.count('function ')
        
        # Classification logic
        if table_indicators >= 3:
            return ChunkType.TABLE_HEAVY
        elif (list_indicators + numbered_list) >= 3:
            return ChunkType.LIST_HEAVY
        elif header_indicators >= 2:
            return ChunkType.HEADER_SECTION
        elif code_indicators >= 2:
            return ChunkType.CODE_BLOCK
        elif table_indicators + list_indicators + header_indicators >= 2:
            return ChunkType.MIXED_CONTENT
        else:
            return ChunkType.NARRATIVE_TEXT


@dataclass
class ChunkMetadata:
    """Enhanced metadata for document chunks."""
    source: str
    file_name: str
    chunk_id: str
    chunk_type: ChunkType
    char_count: int
    word_count: int
    sentence_count: int
    paragraph_count: int
    has_tables: bool
    has_lists: bool
    has_headers: bool
    has_links: bool
    header_level: Optional[int]
    table_count: int
    list_count: int
    link_count: int
    processor: str
    extraction_confidence: float
    semantic_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for storage with Pinecone compatibility."""
        return {
            "source": self.source,
            "file_name": self.file_name,
            "chunk_id": self.chunk_id,
            "chunk_type": self.chunk_type.value,
            "char_count": self.char_count,
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "paragraph_count": self.paragraph_count,
            "has_tables": self.has_tables,
            "has_lists": self.has_lists,
            "has_headers": self.has_headers,
            "has_links": self.has_links,
            "header_level": self.header_level if self.header_level is not None else 0,
            "table_count": self.table_count,
            "list_count": self.list_count,
            "link_count": self.link_count,
            "processor": self.processor,
            "extraction_confidence": self.extraction_confidence,
            "semantic_score": self.semantic_score
        }


class DocumentTypeOptimizer:
    """Optimizes chunking parameters based on document content type."""
    
    CHUNK_CONFIGS = {
        ChunkType.NARRATIVE_TEXT: {
            "chunk_size": 800,
            "chunk_overlap": 50,
            "separators": ["\n\n", "\n", ". ", "? ", "! ", " "]
        },
        ChunkType.TABLE_HEAVY: {
            "chunk_size": 1200,
            "chunk_overlap": 20,
            "separators": ["\n\n", "\n|", "\n"]
        },
        ChunkType.LIST_HEAVY: {
            "chunk_size": 600,
            "chunk_overlap": 30,
            "separators": ["\n\n", "\n- ", "\n* ", "\n• ", "\n"]
        },
        ChunkType.HEADER_SECTION: {
            "chunk_size": 1000,
            "chunk_overlap": 40,
            "separators": ["\n# ", "\n## ", "\n### ", "\n\n", "\n"]
        },
        ChunkType.CODE_BLOCK: {
            "chunk_size": 1500,
            "chunk_overlap": 100,
            "separators": ["\n```", "\n\n", "\n"]
        },
        ChunkType.MIXED_CONTENT: {
            "chunk_size": 900,
            "chunk_overlap": 60,
            "separators": ["\n\n", "\n# ", "\n## ", "\n- ", "\n", ". "]
        }
    }
    
    @classmethod
    def get_optimal_config(cls, chunk_type: ChunkType) -> Dict[str, Any]:
        """Get optimal chunking configuration for content type."""
        return cls.CHUNK_CONFIGS.get(chunk_type, cls.CHUNK_CONFIGS[ChunkType.NARRATIVE_TEXT])


class SemanticAwareChunker:
    """Advanced chunker that preserves semantic structure and context."""
    
    def __init__(self, preserve_tables: bool = True, preserve_lists: bool = True):
        self.preserve_tables = preserve_tables
        self.preserve_lists = preserve_lists
        self.content_classifier = ContentClassifier()
        self.optimizer = DocumentTypeOptimizer()
    
    def analyze_content(self, text: str) -> Dict[str, Any]:
        """Analyze text content for structural elements."""
        analysis = {
            "word_count": len(text.split()),
            "sentence_count": len(re.findall(r'[.!?]+', text)),
            "paragraph_count": len([p for p in text.split('\n\n') if p.strip()]),
            "has_tables": bool(re.search(r'\|.*\|', text)),
            "has_lists": bool(re.search(r'^\s*[-*•]\s', text, re.MULTILINE)),
            "has_headers": bool(re.search(r'^#{1,6}\s', text, re.MULTILINE)),
            "has_links": bool(re.search(r'https?://|www\.|\.com|\.org', text)),
            "table_count": len(re.findall(r'\|.*\|', text)),
            "list_count": len(re.findall(r'^\s*[-*•]\s', text, re.MULTILINE)),
            "link_count": len(re.findall(r'https?://[^\s]+', text))
        }
        
        # Determine header level if present
        header_match = re.search(r'^(#{1,6})\s', text, re.MULTILINE)
        analysis["header_level"] = len(header_match.group(1)) if header_match else None
        
        return analysis
    
    def calculate_semantic_score(self, text: str, analysis: Dict[str, Any]) -> float:
        """Calculate semantic coherence score for a chunk."""
        score = 0.5  # Base score
        
        # Bonus for complete sentences
        if text.strip().endswith(('.', '!', '?')):
            score += 0.1
        
        # Bonus for complete paragraphs
        if '\n\n' in text:
            score += 0.1
        
        # Bonus for structured content
        if analysis["has_tables"] or analysis["has_lists"]:
            score += 0.15
        
        # Penalty for very short chunks
        if analysis["word_count"] < 20:
            score -= 0.2
        
        # Bonus for balanced length
        if 50 <= analysis["word_count"] <= 300:
            score += 0.1
        
        return min(1.0, max(0.0, score))
    
    def split_preserving_structure(self, text: str, chunk_type: ChunkType) -> List[str]:
        """Split text while preserving important structural elements."""
        config = self.optimizer.get_optimal_config(chunk_type)
        
        # Special handling for table-heavy content
        if chunk_type == ChunkType.TABLE_HEAVY and self.preserve_tables:
            return self._split_preserving_tables(text, config)
        
        # Special handling for list-heavy content
        if chunk_type == ChunkType.LIST_HEAVY and self.preserve_lists:
            return self._split_preserving_lists(text, config)
        
        # Default semantic splitting
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config["chunk_size"],
            chunk_overlap=config["chunk_overlap"],
            separators=config["separators"],
            length_function=len,
            is_separator_regex=False
        )
        
        return splitter.split_text(text)
    
    def _split_preserving_tables(self, text: str, config: Dict[str, Any]) -> List[str]:
        """Split text while keeping tables intact within chunks."""
        chunks = []
        current_chunk = ""
        
        # Split by double newlines first
        sections = text.split('\n\n')
        
        for section in sections:
            # Check if section contains a table
            if '|' in section and section.count('|') >= 4:
                # If current chunk + table would be too long, finalize current chunk
                if len(current_chunk) + len(section) > config["chunk_size"] and current_chunk.strip():
                    chunks.append(current_chunk.strip())
                    current_chunk = section
                else:
                    current_chunk += "\n\n" + section if current_chunk else section
            else:
                # Regular text section
                if len(current_chunk) + len(section) > config["chunk_size"] and current_chunk.strip():
                    chunks.append(current_chunk.strip())
                    current_chunk = section
                else:
                    current_chunk += "\n\n" + section if current_chunk else section
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_preserving_lists(self, text: str, config: Dict[str, Any]) -> List[str]:
        """Split text while keeping lists intact within chunks."""
        chunks = []
        current_chunk = ""
        
        lines = text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this line starts a list
            if re.match(r'^\s*[-*•]\s', line) or re.match(r'^\s*\d+\.\s', line):
                # Collect the entire list
                list_items = [line]
                i += 1
                
                while i < len(lines) and (
                    re.match(r'^\s*[-*•]\s', lines[i]) or 
                    re.match(r'^\s*\d+\.\s', lines[i]) or
                    (lines[i].strip() and not lines[i].startswith(' ') == False)
                ):
                    list_items.append(lines[i])
                    i += 1
                
                list_text = '\n'.join(list_items)
                
                # Check if adding this list would exceed chunk size
                if len(current_chunk) + len(list_text) > config["chunk_size"] and current_chunk.strip():
                    chunks.append(current_chunk.strip())
                    current_chunk = list_text
                else:
                    current_chunk += "\n" + list_text if current_chunk else list_text
            else:
                # Regular line
                if len(current_chunk) + len(line) > config["chunk_size"] and current_chunk.strip():
                    chunks.append(current_chunk.strip())
                    current_chunk = line
                else:
                    current_chunk += "\n" + line if current_chunk else line
                i += 1
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks


def enhanced_split_documents(
    documents: List[Document], 
    enhance_metadata: bool = True,
    preserve_structure: bool = True
) -> List[Document]:
    """
    Enhanced document splitting with semantic awareness and rich metadata.
    
    Args:
        documents: List of documents to split
        enhance_metadata: Whether to add enhanced metadata to chunks
        preserve_structure: Whether to preserve document structure
    
    Returns:
        List of semantically-aware document chunks with enhanced metadata
    """
    chunker = SemanticAwareChunker(
        preserve_tables=preserve_structure,
        preserve_lists=preserve_structure
    )
    
    enhanced_chunks = []
    
    print(f"\n📊 Enhanced semantic chunking of {len(documents)} documents...")
    print("="*60)
    
    for doc_idx, document in enumerate(documents):
        print(f"\n🔄 Processing document {doc_idx + 1}/{len(documents)}")
        
        # Analyze content and classify
        content_analysis = chunker.analyze_content(document.page_content)
        chunk_type = chunker.content_classifier.classify_content(document.page_content)
        
        print(f"   📝 Content type: {chunk_type.value}")
        print(f"   📊 Words: {content_analysis['word_count']}, "
              f"Tables: {content_analysis['table_count']}, "
              f"Lists: {content_analysis['list_count']}")
        
        # Split document while preserving structure
        text_chunks = chunker.split_preserving_structure(document.page_content, chunk_type)
        
        print(f"   ✂️  Created {len(text_chunks)} semantic chunks")
        
        # Create enhanced document chunks
        for chunk_idx, chunk_text in enumerate(text_chunks):
            chunk_analysis = chunker.analyze_content(chunk_text)
            semantic_score = chunker.calculate_semantic_score(chunk_text, chunk_analysis)
            
            # Create enhanced metadata
            if enhance_metadata:
                enhanced_metadata = ChunkMetadata(
                    source=document.metadata.get("source", "unknown"),
                    file_name=document.metadata.get("file_name", "unknown"),
                    chunk_id=f"doc_{doc_idx}_chunk_{chunk_idx}",
                    chunk_type=chunker.content_classifier.classify_content(chunk_text),
                    char_count=len(chunk_text),
                    word_count=chunk_analysis["word_count"],
                    sentence_count=chunk_analysis["sentence_count"],
                    paragraph_count=chunk_analysis["paragraph_count"],
                    has_tables=chunk_analysis["has_tables"],
                    has_lists=chunk_analysis["has_lists"],
                    has_headers=chunk_analysis["has_headers"],
                    has_links=chunk_analysis["has_links"],
                    header_level=chunk_analysis["header_level"],
                    table_count=chunk_analysis["table_count"],
                    list_count=chunk_analysis["list_count"],
                    link_count=chunk_analysis["link_count"],
                    processor="semantic_chunker",
                    extraction_confidence=0.85,  # Base confidence
                    semantic_score=semantic_score
                )
                
                # Merge with original metadata
                final_metadata = {**document.metadata, **enhanced_metadata.to_dict()}
            else:
                final_metadata = {
                    **document.metadata,
                    "chunk_id": f"doc_{doc_idx}_chunk_{chunk_idx}",
                    "chunk_type": chunk_type.value,
                    "semantic_score": semantic_score
                }
            
            # Create enhanced document chunk
            enhanced_chunk = Document(
                page_content=chunk_text,
                metadata=final_metadata
            )
            enhanced_chunks.append(enhanced_chunk)
    
    # Summary statistics
    total_chunks = len(enhanced_chunks)
    avg_semantic_score = sum(chunk.metadata.get("semantic_score", 0) for chunk in enhanced_chunks) / total_chunks
    
    chunk_type_counts = {}
    for chunk in enhanced_chunks:
        chunk_type = chunk.metadata.get("chunk_type", "unknown")
        chunk_type_counts[chunk_type] = chunk_type_counts.get(chunk_type, 0) + 1
    
    print(f"\n📈 SEMANTIC CHUNKING SUMMARY")
    print("="*60)
    print(f"📄 Total chunks created: {total_chunks}")
    print(f"🎯 Average semantic score: {avg_semantic_score:.3f}")
    print(f"📊 Chunk type distribution:")
    for chunk_type, count in chunk_type_counts.items():
        percentage = (count / total_chunks) * 100
        print(f"   • {chunk_type}: {count} ({percentage:.1f}%)")
    print("="*60)
    
    return enhanced_chunks