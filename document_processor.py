"""
Document Processing Module for RAG System

This module provides comprehensive document processing capabilities including:
- Multi-format document loading (PDF, DOCX, TXT, MD, etc.)
- Text chunking with various strategies
- Metadata extraction and management
- Document preprocessing and cleaning

Key Components:
- DocumentLoader: Abstract base class for document loaders
- Specific loaders: PDFLoader, DOCXLoader, TextLoader, etc.
- TextChunker: Handles text splitting with overlap
- DocumentProcessor: Main processing pipeline
- Document: Data model for processed documents

Technologies Used:
- LangChain: For document loading and text splitting
- pypdf: For PDF processing
- python-docx: For Word document processing
- Pydantic: For data validation and models
"""

import os
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field, field_validator
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter
)

# Optional imports - will handle gracefully if not available
try:
    from langchain_community.document_loaders import (
        PyPDFLoader,
        UnstructuredWordDocumentLoader,
        TextLoader as LangChainTextLoader
    )
    HAS_LANGCHAIN_LOADERS = True
except ImportError:
    HAS_LANGCHAIN_LOADERS = False

try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

from config import get_config


class DocumentType(Enum):
    """Enumeration of supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    UNKNOWN = "unknown"


class ChunkingStrategy(Enum):
    """Enumeration of text chunking strategies."""
    RECURSIVE = "recursive"
    CHARACTER = "character"
    TOKEN = "token"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"


@dataclass
class DocumentMetadata:
    """
    Metadata container for processed documents.
    
    This class stores important information about the source document
    and processing parameters used.
    """
    filename: str
    filepath: str
    file_size: int
    file_hash: str
    document_type: DocumentType
    processed_at: datetime
    chunk_count: int
    total_characters: int
    chunking_strategy: ChunkingStrategy
    chunk_size: int
    chunk_overlap: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for storage."""
        return {
            "filename": self.filename,
            "filepath": self.filepath,
            "file_size": self.file_size,
            "file_hash": self.file_hash,
            "document_type": self.document_type.value,
            "processed_at": self.processed_at.isoformat(),
            "chunk_count": self.chunk_count,
            "total_characters": self.total_characters,
            "chunking_strategy": self.chunking_strategy.value,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }


class DocumentChunk(BaseModel):
    """
    Represents a chunk of text from a processed document.
    
    Each chunk contains the text content, metadata about its source,
    and position information within the original document.
    """
    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    content: str = Field(..., description="Text content of the chunk")
    chunk_index: int = Field(..., description="Position of chunk in document")
    source_document: str = Field(..., description="Source document filename")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('content')
    def validate_content(cls, v):
        """Ensure content is not empty after stripping."""
        if not v or not v.strip():
            raise ValueError("Chunk content cannot be empty")
        return v.strip()
    
    def __str__(self) -> str:
        """String representation of the chunk."""
        return f"DocumentChunk(id={self.chunk_id}, source={self.source_document}, length={len(self.content)})"


class DocumentLoader(ABC):
    """
    Abstract base class for document loaders.
    
    This class defines the interface that all document loaders must implement.
    It provides common functionality for file validation and error handling.
    """
    
    def __init__(self, supported_extensions: List[str]):
        """Initialize the loader with supported file extensions."""
        self.supported_extensions = [ext.lower() for ext in supported_extensions]
    
    def can_load(self, file_path: Union[str, Path]) -> bool:
        """Check if this loader can handle the given file."""
        file_path = Path(file_path)
        return file_path.suffix.lower() in self.supported_extensions
    
    def _validate_file(self, file_path: Union[str, Path]) -> Path:
        """Validate that the file exists and is readable."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        if not os.access(file_path, os.R_OK):
            raise PermissionError(f"File is not readable: {file_path}")
        
        return file_path
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of the file for change detection."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    @abstractmethod
    def load_content(self, file_path: Union[str, Path]) -> str:
        """Load and return the text content from the file."""
        pass
    
    def get_document_type(self, file_path: Union[str, Path]) -> DocumentType:
        """Determine the document type from file extension."""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        type_mapping = {
            '.pdf': DocumentType.PDF,
            '.docx': DocumentType.DOCX,
            '.doc': DocumentType.DOC,
            '.txt': DocumentType.TXT,
            '.md': DocumentType.MD,
            '.html': DocumentType.HTML,
            '.json': DocumentType.JSON,
            '.csv': DocumentType.CSV
        }
        
        return type_mapping.get(extension, DocumentType.UNKNOWN)


class TextLoader(DocumentLoader):
    """
    Loader for plain text files (.txt, .md).
    
    This loader handles basic text files with various encodings.
    """
    
    def __init__(self):
        super().__init__(['.txt', '.md', '.text'])
        self.encoding_attempts = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    
    def load_content(self, file_path: Union[str, Path]) -> str:
        """Load content from a text file with encoding detection."""
        file_path = self._validate_file(file_path)
        
        # Try different encodings
        for encoding in self.encoding_attempts:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    
                # Validate that we got meaningful content
                if content.strip():
                    return content
                    
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        raise ValueError(f"Could not decode file {file_path} with any supported encoding")


class PDFLoader(DocumentLoader):
    """
    Loader for PDF files.
    
    This loader extracts text from PDF files using pypdf or LangChain loaders.
    """
    
    def __init__(self):
        super().__init__(['.pdf'])
    
    def load_content(self, file_path: Union[str, Path]) -> str:
        """Load content from a PDF file."""
        file_path = self._validate_file(file_path)
        
        # Try LangChain PyPDFLoader first (more robust)
        if HAS_LANGCHAIN_LOADERS:
            try:
                loader = PyPDFLoader(str(file_path))
                pages = loader.load()
                return "\n\n".join([page.page_content for page in pages])
            except Exception as e:
                print(f"Warning: LangChain PDF loader failed: {e}")
        
        # Fallback to direct pypdf usage
        if HAS_PYPDF:
            try:
                import pypdf
                content_parts = []
                
                with open(file_path, 'rb') as file:
                    pdf_reader = pypdf.PdfReader(file)
                    
                    for page_num, page in enumerate(pdf_reader.pages):
                        try:
                            text = page.extract_text()
                            if text.strip():
                                content_parts.append(text)
                        except Exception as e:
                            print(f"Warning: Could not extract text from page {page_num}: {e}")
                
                if content_parts:
                    return "\n\n".join(content_parts)
                else:
                    raise ValueError("No text content could be extracted from PDF")
                    
            except Exception as e:
                raise ValueError(f"Failed to load PDF content: {e}")
        
        raise ImportError("PDF loading requires pypdf or langchain-community packages")


class DOCXLoader(DocumentLoader):
    """
    Loader for Microsoft Word documents (.docx).
    
    This loader extracts text from Word documents using python-docx or LangChain.
    """
    
    def __init__(self):
        super().__init__(['.docx', '.doc'])
    
    def load_content(self, file_path: Union[str, Path]) -> str:
        """Load content from a Word document."""
        file_path = self._validate_file(file_path)
        
        # Try LangChain loader first
        if HAS_LANGCHAIN_LOADERS:
            try:
                loader = UnstructuredWordDocumentLoader(str(file_path))
                docs = loader.load()
                return "\n\n".join([doc.page_content for doc in docs])
            except Exception as e:
                print(f"Warning: LangChain DOCX loader failed: {e}")
        
        # Fallback to direct python-docx usage
        if HAS_DOCX:
            try:
                doc = DocxDocument(file_path)
                content_parts = []
                
                for paragraph in doc.paragraphs:
                    text = paragraph.text.strip()
                    if text:
                        content_parts.append(text)
                
                if content_parts:
                    return "\n\n".join(content_parts)
                else:
                    raise ValueError("No text content found in Word document")
                    
            except Exception as e:
                raise ValueError(f"Failed to load DOCX content: {e}")
        
        raise ImportError("DOCX loading requires python-docx or langchain-community packages")


class TextChunker:
    """
    Handles text chunking with various strategies.
    
    This class provides different methods for splitting text into manageable chunks
    while preserving semantic meaning and maintaining appropriate overlap.
    """
    
    def __init__(self, strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE,
                 chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the text chunker.
        
        Args:
            strategy: Chunking strategy to use
            chunk_size: Target size for each chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._splitter = self._create_splitter()
    
    def _create_splitter(self):
        """Create the appropriate text splitter based on strategy."""
        if self.strategy == ChunkingStrategy.RECURSIVE:
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
        elif self.strategy == ChunkingStrategy.CHARACTER:
            return CharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separator="\n"
            )
        elif self.strategy == ChunkingStrategy.TOKEN:
            return TokenTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        else:
            # Default to recursive for unsupported strategies
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
    
    def chunk_text(self, text: str, source_document: str) -> List[DocumentChunk]:
        """
        Split text into chunks and create DocumentChunk objects.
        
        Args:
            text: Text content to chunk
            source_document: Name of the source document
            
        Returns:
            List of DocumentChunk objects
        """
        if not text or not text.strip():
            return []
        
        # Split the text
        chunks = self._splitter.split_text(text)
        
        # Create DocumentChunk objects
        document_chunks = []
        for i, chunk_content in enumerate(chunks):
            if chunk_content.strip():  # Only include non-empty chunks
                chunk_id = f"{source_document}_{i:04d}"
                
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    content=chunk_content,
                    chunk_index=i,
                    source_document=source_document,
                    metadata={
                        "chunking_strategy": self.strategy.value,
                        "chunk_size": self.chunk_size,
                        "chunk_overlap": self.chunk_overlap,
                        "character_count": len(chunk_content)
                    }
                )
                document_chunks.append(chunk)
        
        return document_chunks


class DocumentProcessor:
    """
    Main document processing pipeline.
    
    This class orchestrates the document processing workflow:
    1. Load documents using appropriate loaders
    2. Extract and clean text content
    3. Chunk text into manageable pieces
    4. Generate metadata
    5. Return processed document chunks
    """
    
    def __init__(self, config=None):
        """
        Initialize the document processor.
        
        Args:
            config: Configuration object (uses global config if None)
        """
        self.config = config or get_config()
        self.loaders = self._initialize_loaders()
        self.chunker = TextChunker(
            strategy=ChunkingStrategy.RECURSIVE,
            chunk_size=self.config.vector_store.chunk_size,
            chunk_overlap=self.config.vector_store.chunk_overlap
        )
    
    def _initialize_loaders(self) -> Dict[DocumentType, DocumentLoader]:
        """Initialize document loaders for different file types."""
        loaders = {}
        
        # Always available loaders
        text_loader = TextLoader()
        loaders[DocumentType.TXT] = text_loader
        loaders[DocumentType.MD] = text_loader
        
        # Conditional loaders based on dependencies
        if HAS_PYPDF or HAS_LANGCHAIN_LOADERS:
            loaders[DocumentType.PDF] = PDFLoader()
        
        if HAS_DOCX or HAS_LANGCHAIN_LOADERS:
            docx_loader = DOCXLoader()
            loaders[DocumentType.DOCX] = docx_loader
            loaders[DocumentType.DOC] = docx_loader
        
        return loaders
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        formats = []
        for loader in self.loaders.values():
            formats.extend(loader.supported_extensions)
        return sorted(list(set(formats)))
    
    def can_process(self, file_path: Union[str, Path]) -> bool:
        """Check if the processor can handle the given file."""
        file_path = Path(file_path)
        document_type = self._get_document_type(file_path)
        return document_type in self.loaders
    
    def _get_document_type(self, file_path: Path) -> DocumentType:
        """Determine document type from file extension."""
        extension = file_path.suffix.lower()
        
        type_mapping = {
            '.pdf': DocumentType.PDF,
            '.docx': DocumentType.DOCX,
            '.doc': DocumentType.DOC,
            '.txt': DocumentType.TXT,
            '.md': DocumentType.MD,
            '.html': DocumentType.HTML,
            '.json': DocumentType.JSON,
            '.csv': DocumentType.CSV
        }
        
        return type_mapping.get(extension, DocumentType.UNKNOWN)
    
    def process_document(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Process a single document and return chunks with metadata.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary containing chunks and metadata
            
        Raises:
            ValueError: If file cannot be processed
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine document type and get appropriate loader
        document_type = self._get_document_type(file_path)
        
        if document_type not in self.loaders:
            raise ValueError(f"Unsupported document type: {document_type.value} for file {file_path}")
        
        loader = self.loaders[document_type]
        
        # Load content
        try:
            content = loader.load_content(file_path)
        except Exception as e:
            raise ValueError(f"Failed to load content from {file_path}: {e}")
        
        if not content or not content.strip():
            raise ValueError(f"No content extracted from {file_path}")
        
        # Chunk the content
        chunks = self.chunker.chunk_text(content, file_path.name)
        
        # Generate metadata
        metadata = DocumentMetadata(
            filename=file_path.name,
            filepath=str(file_path.absolute()),
            file_size=file_path.stat().st_size,
            file_hash=loader._calculate_file_hash(file_path),
            document_type=document_type,
            processed_at=datetime.now(),
            chunk_count=len(chunks),
            total_characters=len(content),
            chunking_strategy=self.chunker.strategy,
            chunk_size=self.chunker.chunk_size,
            chunk_overlap=self.chunker.chunk_overlap
        )
        
        return {
            "chunks": chunks,
            "metadata": metadata,
            "original_content": content
        }
    
    def process_directory(self, directory_path: Union[str, Path], 
                         recursive: bool = True) -> List[Dict[str, Any]]:
        """
        Process all supported documents in a directory.
        
        Args:
            directory_path: Path to the directory
            recursive: Whether to process subdirectories
            
        Returns:
            List of processing results for each document
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists() or not directory_path.is_dir():
            raise ValueError(f"Invalid directory: {directory_path}")
        
        results = []
        
        # Get file pattern based on recursive flag
        pattern = "**/*" if recursive else "*"
        
        for file_path in directory_path.glob(pattern):
            if file_path.is_file() and self.can_process(file_path):
                try:
                    result = self.process_document(file_path)
                    result["status"] = "success"
                    results.append(result)
                except Exception as e:
                    results.append({
                        "filepath": str(file_path),
                        "status": "error",
                        "error": str(e)
                    })
        
        return results


# Utility functions
def create_document_processor(config=None) -> DocumentProcessor:
    """
    Factory function to create a DocumentProcessor instance.
    
    Args:
        config: Configuration object (optional)
        
    Returns:
        DocumentProcessor instance
    """
    return DocumentProcessor(config)


def get_supported_formats() -> List[str]:
    """
    Get list of all supported document formats.
    
    Returns:
        List of supported file extensions
    """
    processor = create_document_processor()
    return processor.get_supported_formats() 