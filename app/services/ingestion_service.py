"""
Ingestion service for RAG: PDF -> chunks -> embeddings -> ChromaDB

This module provides an async-friendly ingestion function that:
- Loads a PDF via LangChain's `PyPDFLoader`
- Splits text into chunks via `RecursiveCharacterTextSplitter`
- Generates embeddings using Google's GenAI embeddings adapter (langchain-google-genai)
- Persists vectors into a ChromaDB collection stored at the path configured in `app.config`

Note: heavy/blocking operations (model calls, I/O) are executed via `asyncio.to_thread`
to avoid blocking the event loop.
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

from app.config import settings



logger = logging.getLogger(__name__)








__all__ = ["ingest_pdf"]
"""
Service for ingesting documents (PDFs, text) into the vector store.
Orchestrates PDF processing, chunking, embedding, and ChromaDB storage.
"""

# ... (previous imports)
from typing import List, Dict, Any, Optional

from app.services.pdf_processor import PDFProcessor
from app.services.embedding_service import EmbeddingService
from app.utils.faiss_store import get_vector_store
import logging

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Manages the ingestion pipeline for various document types into FAISS.
    """

    def __init__(self, collection_name: str = "legalhub_documents"):
        self.pdf_processor = PDFProcessor()
        self.embedding_service = EmbeddingService()
        self.vector_store = None
        self.collection_name = collection_name

    def _ensure_collection(self):
        """Lazily initialize FAISS vector store."""
        if self.vector_store is not None:
            return
        self.vector_store = get_vector_store(self.collection_name)

    async def ingest_document(
        self,
        content: bytes | str,
        document_id: str,
        document_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Ingests a document into the FAISS vector store.

        Args:
            content: The raw content of the document (bytes for PDF, str for text).
            document_id: A unique identifier for the document.
            document_type: The type of document (e.g., "pdf", "firestore_article", "web_page").
            metadata: Optional dictionary of additional metadata for the document.

        Returns:
            A list of IDs of the chunks added to the vector store.
        """
        if metadata is None:
            metadata = {}

        full_text = ""
        if document_type == "pdf" and isinstance(content, bytes):
            logger.info(f"Processing PDF document: {document_id}")
            extracted_text, pdf_metadata = self.pdf_processor.extract_text_from_pdf(
                content
            )
            full_text = extracted_text
            metadata.update(pdf_metadata)
        elif isinstance(content, str):
            logger.info(f"Processing text document: {document_id}")
            full_text = content
        else:
            raise ValueError(
                f"Unsupported content type or document type: {document_type}"
            )

        if not full_text.strip():
            logger.warning(
                f"Document {document_id} has no extractable text. Skipping ingestion."
            )
            return []

        # Add document_id and document_type to metadata for all chunks
        metadata["document_id"] = document_id
        metadata["document_type"] = document_type

        # Ensure vector store exists
        self._ensure_collection()

        # Chunk the text
        chunks = self.embedding_service.semantic_chunk_text(full_text)

        # Prepare data for FAISS
        documents_for_faiss = []
        chunk_ids = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"
            
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_id"] = chunk_id
            chunk_metadata["chunk_index"] = i
            chunk_metadata["text_length"] = len(chunk["content"])
            
            # Combine content and metadata into a single dict for FAISS store
            doc = {
                "id": chunk_id,
                "content": chunk["content"],
                "source": metadata.get("source", "unknown"),
                **chunk_metadata
            }
            
            documents_for_faiss.append(doc)
            chunk_ids.append(chunk_id)

        if not documents_for_faiss:
            logger.warning(
                f"No chunks generated for document {document_id}. Skipping embedding and storage."
            )
            return []

        # Add to FAISS
        try:
            # Note: FAISSVectorStore handles embedding generation internally using SentenceTransformer
            # if we pass raw text content.
            self.vector_store.add_documents(documents_for_faiss)
            
            logger.info(
                f"Successfully ingested {len(chunk_ids)} chunks for document {document_id} into FAISS."
            )
            return chunk_ids
        except Exception as e:
            logger.error(f"Failed to ingest document {document_id} into FAISS: {e}")
            raise

    async def ingest_firestore_articles(self) -> int:
        """
        Fetches all articles from Firestore and ingests them into FAISS.
        """
        from app.services.firebase_service import (
            firebase_service,
        )  # Import here to avoid circular dependency

        articles = await firebase_service.get_all_articles()

        ingested_count = 0
        for article in articles:
            try:
                # Use article_id as document_id for consistent tracking
                await self.ingest_document(
                    content=article.content,
                    document_id=article.article_id,
                    document_type="firestore_article",
                    metadata={
                        "title": article.title,
                        "author_id": article.author_id,
                        "tags": article.tags,
                        "published": article.published,
                        "created_at": (
                            article.created_at.isoformat()
                            if article.created_at
                            else None
                        ),
                        "updated_at": (
                            article.updated_at.isoformat()
                            if article.updated_at
                            else None
                        ),
                    },
                )
                ingested_count += 1
            except Exception as e:
                logger.error(
                    f"Failed to ingest Firestore article {article.article_id}: {e}"
                )
        logger.info(
            f"Successfully ingested {ingested_count} Firestore articles into FAISS."
        )
        return ingested_count


# Global instance of the IngestionService
ingestion_service = IngestionService()
