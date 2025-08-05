"""
Vector Store Module for RAG System

This module provides vector storage and retrieval capabilities for the RAG system.
Supports ChromaDB for persistent storage and FAISS for high-performance similarity search.
"""

import os
import json
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime

import numpy as np
from pydantic import BaseModel, Field, field_validator

# Optional imports with graceful fallbacks
try:
    import chromadb
    from chromadb.config import Settings

    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

try:
    import faiss

    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

try:
    from langchain_openai import OpenAIEmbeddings

    HAS_OPENAI_EMBEDDINGS = True
except ImportError:
    HAS_OPENAI_EMBEDDINGS = False

from config import get_config
from document_processor import DocumentChunk, DocumentMetadata


class EmbeddingResult(BaseModel):
    """Result of embedding generation."""

    embedding: List[float] = Field(..., description="The embedding vector")
    model: str = Field(..., description="Model used for embedding")
    dimensions: int = Field(..., description="Dimensionality of the embedding")

    @field_validator("embedding")
    def validate_embedding(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Embedding cannot be empty")
        return v


class SearchResult(BaseModel):
    """Result of similarity search."""

    chunk: DocumentChunk = Field(..., description="Retrieved document chunk")
    score: float = Field(..., description="Similarity score (0-1)")
    rank: int = Field(..., description="Rank in search results")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Search metadata"
    )

    @field_validator("score")
    def validate_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")
        return v


class EmbeddingManager:
    """Manages embedding generation using OpenAI."""

    def __init__(self, config=None):
        self.config = config or get_config()
        self.embeddings = None
        self._initialize_embeddings()

    def _initialize_embeddings(self):
        """Initialize OpenAI embeddings."""
        if HAS_OPENAI_EMBEDDINGS:
            try:
                self.embeddings = OpenAIEmbeddings(
                    model=self.config.vector_store.embedding_model,
                    openai_api_key=os.getenv("OPENAI_API_KEY"),
                )
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI embeddings: {e}")

    def generate_embedding(self, text: str) -> EmbeddingResult:
        """Generate embedding for text."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if not self.embeddings:
            raise ValueError("No embedding provider available")

        try:
            embedding = self.embeddings.embed_query(text.strip())
            return EmbeddingResult(
                embedding=embedding,
                model=self.config.vector_store.embedding_model,
                dimensions=len(embedding),
            )
        except Exception as e:
            raise ValueError(f"Failed to generate embedding: {e}")

    def generate_embeddings_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        if not self.embeddings:
            raise ValueError("No embedding provider available")

        try:
            embeddings = self.embeddings.embed_documents(texts)
            return [
                EmbeddingResult(
                    embedding=embedding,
                    model=self.config.vector_store.embedding_model,
                    dimensions=len(embedding),
                )
                for embedding in embeddings
            ]
        except Exception as e:
            raise ValueError(f"Failed to generate batch embeddings: {e}")


class VectorStore(ABC):
    """Abstract base class for vector stores."""

    def __init__(self, config=None):
        self.config = config or get_config()
        self.embedding_manager = EmbeddingManager(config)

    @abstractmethod
    def add_documents(
        self, chunks: List[DocumentChunk], metadata: Optional[DocumentMetadata] = None
    ) -> bool:
        """Add document chunks to the vector store."""
        pass

    @abstractmethod
    def similarity_search(self, query: str, k: int = 5, **kwargs) -> List[SearchResult]:
        """Perform similarity search for the query."""
        pass

    @abstractmethod
    def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents from the vector store."""
        pass

    @abstractmethod
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection."""
        pass


class ChromaVectorStore(VectorStore):
    """ChromaDB-based vector store implementation."""

    def __init__(
        self,
        collection_name: str = "rag_documents",
        persist_directory: str = "./chroma_db",
        config=None,
    ):
        super().__init__(config)

        if not HAS_CHROMADB:
            raise ImportError("ChromaDB required: pip install chromadb")

        self.collection_name = collection_name
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False),
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"description": "RAG document chunks"}
        )

    def add_documents(
        self, chunks: List[DocumentChunk], metadata: Optional[DocumentMetadata] = None
    ) -> bool:
        """Add document chunks to ChromaDB."""
        if not chunks:
            return True

        try:
            # Generate embeddings
            texts = [chunk.content for chunk in chunks]
            embedding_results = self.embedding_manager.generate_embeddings_batch(texts)

            # Prepare data for ChromaDB
            ids = []
            embeddings = []
            documents = []
            metadatas = []

            for chunk, embedding_result in zip(chunks, embedding_results):
                chunk_id = f"{chunk.source_document}_{chunk.chunk_index}_{uuid.uuid4().hex[:8]}"
                ids.append(chunk_id)
                embeddings.append(embedding_result.embedding)
                documents.append(chunk.content)

                # Prepare metadata
                chunk_metadata = {
                    "chunk_id": chunk.chunk_id,
                    "source_document": chunk.source_document,
                    "chunk_index": chunk.chunk_index,
                    "character_count": len(chunk.content),
                    "added_at": datetime.now().isoformat(),
                }

                if metadata:
                    chunk_metadata.update(
                        {
                            "document_type": metadata.document_type.value,
                            "file_size": metadata.file_size,
                            "file_hash": metadata.file_hash,
                        }
                    )

                chunk_metadata.update(chunk.metadata)
                metadatas.append(chunk_metadata)

            # Add to ChromaDB
            self.collection.add(
                ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
            )

            return True

        except Exception as e:
            print(f"Error adding documents to ChromaDB: {e}")
            return False

    def similarity_search(self, query: str, k: int = 5, **kwargs) -> List[SearchResult]:
        """Perform similarity search in ChromaDB."""
        if not query or not query.strip():
            return []

        try:
            query_embedding = self.embedding_manager.generate_embedding(query.strip())

            results = self.collection.query(
                query_embeddings=[query_embedding.embedding],
                n_results=k,
                include=["documents", "metadatas", "distances"],
                **kwargs,
            )

            search_results = []

            if results["documents"] and len(results["documents"]) > 0:
                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if results["metadatas"] else []
                distances = results["distances"][0] if results["distances"] else []

                for rank, (doc, meta, distance) in enumerate(
                    zip(documents, metadatas, distances)
                ):
                    # Convert distance to similarity score
                    score = max(0.0, min(1.0, 1.0 - distance))

                    chunk = DocumentChunk(
                        chunk_id=meta.get("chunk_id", f"unknown_{rank}"),
                        content=doc,
                        chunk_index=meta.get("chunk_index", rank),
                        source_document=meta.get("source_document", "unknown"),
                        metadata=meta,
                    )

                    search_result = SearchResult(
                        chunk=chunk,
                        score=score,
                        rank=rank,
                        metadata={"distance": distance, "search_query": query},
                    )

                    search_results.append(search_result)

            return search_results

        except Exception as e:
            print(f"Error performing similarity search: {e}")
            return []

    def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents from ChromaDB."""
        if not document_ids:
            return True

        try:
            self.collection.delete(where={"source_document": {"$in": document_ids}})
            return True
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get ChromaDB collection statistics."""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": str(self.persist_directory),
                "backend": "ChromaDB",
            }
        except Exception as e:
            return {"error": str(e)}


class FAISSVectorStore(VectorStore):
    """FAISS-based vector store implementation."""

    def __init__(self, index_path: str = "./faiss_index", config=None):
        super().__init__(config)

        if not HAS_FAISS:
            raise ImportError("FAISS required: pip install faiss-cpu")

        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index = None
        self.documents = []
        self.dimension = None

    def add_documents(
        self, chunks: List[DocumentChunk], metadata: Optional[DocumentMetadata] = None
    ) -> bool:
        """Add document chunks to FAISS index."""
        if not chunks:
            return True

        try:
            # Generate embeddings
            texts = [chunk.content for chunk in chunks]
            embedding_results = self.embedding_manager.generate_embeddings_batch(texts)

            # Convert to numpy array
            embeddings = np.array(
                [result.embedding for result in embedding_results], dtype=np.float32
            )

            # Initialize index if needed
            if self.index is None:
                self.dimension = embeddings.shape[1]
                self.index = faiss.IndexFlatIP(self.dimension)

            # Add embeddings
            self.index.add(embeddings)

            # Store document data
            for chunk, embedding_result in zip(chunks, embedding_results):
                doc_data = {
                    "chunk": chunk,
                    "embedding_result": embedding_result,
                    "metadata": metadata,
                    "added_at": datetime.now().isoformat(),
                }
                self.documents.append(doc_data)

            return True

        except Exception as e:
            print(f"Error adding documents to FAISS: {e}")
            return False

    def similarity_search(self, query: str, k: int = 5, **kwargs) -> List[SearchResult]:
        """Perform similarity search in FAISS index."""
        if (
            not query
            or not query.strip()
            or self.index is None
            or len(self.documents) == 0
        ):
            return []

        try:
            query_embedding = self.embedding_manager.generate_embedding(query.strip())
            query_vector = np.array([query_embedding.embedding], dtype=np.float32)

            k = min(k, len(self.documents))
            scores, indices = self.index.search(query_vector, k)

            search_results = []
            for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.documents):
                    doc_data = self.documents[idx]
                    normalized_score = max(0.0, min(1.0, float(score)))

                    search_result = SearchResult(
                        chunk=doc_data["chunk"],
                        score=normalized_score,
                        rank=rank,
                        metadata={"faiss_index": int(idx), "raw_score": float(score)},
                    )

                    search_results.append(search_result)

            return search_results

        except Exception as e:
            print(f"Error performing FAISS similarity search: {e}")
            return []

    def delete_documents(self, document_ids: List[str]) -> bool:
        """FAISS doesn't support direct deletion."""
        print(
            "Warning: FAISS doesn't support direct deletion. Consider rebuilding the index."
        )
        return False

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get FAISS index statistics."""
        return {
            "document_count": len(self.documents),
            "index_dimension": self.dimension,
            "index_size": self.index.ntotal if self.index else 0,
            "backend": "FAISS",
        }


class DocumentRetriever:
    """High-level document retrieval interface."""

    def __init__(self, vector_store: VectorStore, config=None):
        self.vector_store = vector_store
        self.config = config or get_config()

    def retrieve_documents(
        self, query: str, k: int = 5, min_score: float = 0.0
    ) -> List[SearchResult]:
        """Retrieve documents for the given query."""
        if not query or not query.strip():
            return []

        results = self.vector_store.similarity_search(query, k=k)

        # Apply score filtering
        if min_score > 0.0:
            results = [result for result in results if result.score >= min_score]

        return results

    def add_documents_from_processor(self, processing_result: Dict[str, Any]) -> bool:
        """Add documents from document processor result."""
        chunks = processing_result.get("chunks", [])
        metadata = processing_result.get("metadata")

        if not chunks:
            return True

        return self.vector_store.add_documents(chunks, metadata)

    def get_stats(self) -> Dict[str, Any]:
        """Get retrieval system statistics."""
        return self.vector_store.get_collection_stats()


# Factory functions
def create_vector_store(config=None, **kwargs) -> VectorStore:
    """Factory function to create vector store instances."""
    config = config or get_config()

    # Get vector store type from config
    store_type = getattr(config.vector_store, "vector_store_type", "chroma")

    if store_type.lower() == "chroma":
        return ChromaVectorStore(config=config, **kwargs)
    elif store_type.lower() == "faiss":
        return FAISSVectorStore(config=config, **kwargs)
    else:
        raise ValueError(f"Unsupported vector store type: {store_type}")


def create_retriever(
    vector_store: VectorStore = None, config=None, **kwargs
) -> DocumentRetriever:
    """Factory function to create document retriever instances."""
    if vector_store is None:
        vector_store = create_vector_store(config, **kwargs)
    return DocumentRetriever(vector_store, config)
