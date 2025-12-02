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

try:
    from langchain_community.document_loaders import PyPDFLoader
except ImportError:
    from langchain.document_loaders import PyPDFLoader

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

# Embedding adapter: try to import the google-genai LangChain integration with fallbacks
try:
    # Preferred integration provided by `langchain-google-genai`
    from langchain_google_genai import GoogleGenAIEmbeddings  # type: ignore
except Exception:
    try:
        # Fallback to older packaging
        from langchain.embeddings import GoogleGenAIEmbeddings  # type: ignore
    except Exception:
        GoogleGenAIEmbeddings = None  # type: ignore

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
except Exception:  # pragma: no cover - import-time fallback
    chromadb = None  # type: ignore
    ChromaSettings = None  # type: ignore

logger = logging.getLogger(__name__)


_chroma_client = None


def _get_chroma_client():
    """Lazy singleton Chroma client using the configured `CHROMADB_PATH`."""
    global _chroma_client
    if _chroma_client is not None:
        return _chroma_client

    if chromadb is None or ChromaSettings is None:
        raise RuntimeError("chromadb is not installed. Please add 'chromadb' to requirements.")

    settings_obj = ChromaSettings(persist_directory=settings.CHROMADB_PATH)
    client = chromadb.Client(settings=settings_obj)
    _chroma_client = client
    return _chroma_client


async def ingest_pdf(
    pdf_path: str,
    collection_name: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    metadata: Optional[dict] = None,
):
    """
    Ingest a PDF file into a persistent ChromaDB collection.

    Args:
        pdf_path: Local path to the PDF file to ingest.
        collection_name: Name of the ChromaDB collection to store vectors in.
        chunk_size: Size of each text chunk (characters).
        chunk_overlap: Overlap between adjacent chunks (characters).
        metadata: Optional metadata to attach to each chunk.

    Returns:
        dict: summary with `n_chunks` and `collection` name.
    """

    # 1) Load PDF (blocking) in a thread
    def _load_pdf(path: str):
        loader = PyPDFLoader(path)
        docs = loader.load()
        return docs

    logger.info("Loading PDF: %s", pdf_path)
    docs = await asyncio.to_thread(_load_pdf, pdf_path)

    # 2) Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def _split(docs):
        return splitter.split_documents(docs)

    logger.info("Splitting into chunks: size=%s overlap=%s", chunk_size, chunk_overlap)
    chunks = await asyncio.to_thread(_split, docs)

    texts = [d.page_content for d in chunks]
    metadatas = [dict(d.metadata or {}) for d in chunks]
    if metadata:
        # merge provided metadata into each chunk's metadata
        for m in metadatas:
            m.update(metadata)

    n_chunks = len(texts)
    logger.info("Generated %d chunks from PDF", n_chunks)

    # 3) Create embeddings
    if GoogleGenAIEmbeddings is None:
        raise RuntimeError(
            "GoogleGenAIEmbeddings not available. Ensure 'langchain-google-genai' is installed."
        )

    def _make_embeddings(texts: List[str]):
        # instantiate with API key from config if available
        kwargs = {}
        if getattr(settings, "GOOGLE_API_KEY", None):
            kwargs["api_key"] = settings.GOOGLE_API_KEY
        emb = GoogleGenAIEmbeddings(**kwargs)
        # embedding method name depends on integration; try common names
        if hasattr(emb, "embed_documents"):
            return emb.embed_documents(texts)
        if hasattr(emb, "embed"):
            # some adapters use embed
            return [emb.embed(t) for t in texts]
        raise RuntimeError("Embedding adapter has no known embed method")

    logger.info("Generating embeddings for %d chunks", n_chunks)
    embeddings = await asyncio.to_thread(_make_embeddings, texts)

    # 4) Save to Chroma
    client = _get_chroma_client()
    collection = client.get_collection(name=collection_name)

    # If collection doesn't exist, create it
    if collection is None:
        collection = client.create_collection(name=collection_name)

    # Prepare ids
    ids = [f"{collection_name}-{i}" for i in range(n_chunks)]

    # Upsert into collection (the API differs between chroma versions; attempt common methods)
    try:
        collection.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)
    except Exception:
        # older/newer client might use upsert
        collection.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)

    # persist to disk
    try:
        client.persist()
    except Exception:
        # some clients persist on the collection
        try:
            collection.persist()
        except Exception:
            logger.debug("Chroma client/collection has no explicit persist method; continuing")

    logger.info("Ingestion complete: collection=%s chunks=%d", collection_name, n_chunks)
    return {"collection": collection_name, "n_chunks": n_chunks}


__all__ = ["ingest_pdf"]
"""
Service for ingesting documents (PDFs, text) into the vector store.
Orchestrates PDF processing, chunking, embedding, and ChromaDB storage.
"""

from typing import List, Dict, Any, Optional

from app.services.pdf_processor import PDFProcessor
from app.services.embedding_service import EmbeddingService
from app.utils.vector_store import (
    get_chroma_client,
    get_or_create_collection,
    get_sentence_transformer_ef,
)
import logging

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Manages the ingestion pipeline for various document types into ChromaDB.
    """

    def __init__(self, collection_name: str = "legal_documents"):
        self.pdf_processor = PDFProcessor()
        self.embedding_service = EmbeddingService()
        # Defer creating chroma client and collection until actually needed
        self.chroma_client = None
        self.collection = None
        self.collection_name = collection_name

    def _ensure_collection(self):
        """Lazily initialize Chroma client and collection."""
        if self.collection is not None:
            return
        self.chroma_client = get_chroma_client()
        # get_or_create_collection will lazily initialize embedding function
        self.collection = get_or_create_collection(
            collection_name=self.collection_name, client=self.chroma_client
        )

    async def ingest_document(
        self,
        content: bytes | str,
        document_id: str,
        document_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Ingests a document into the ChromaDB vector store.

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

        # Ensure vector store collection exists
        self._ensure_collection()

        # Chunk the text
        chunks = self.embedding_service.semantic_chunk_text(full_text)

        # Prepare data for ChromaDB
        chunk_contents: List[str] = []
        chunk_metadatas: List[Dict[str, Any]] = []
        chunk_ids: List[str] = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"
            chunk_contents.append(chunk["content"])

            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_id"] = chunk_id
            chunk_metadata["chunk_index"] = i
            chunk_metadata["text_length"] = len(chunk["content"])
            chunk_metadatas.append(chunk_metadata)
            chunk_ids.append(chunk_id)

        if not chunk_contents:
            logger.warning(
                f"No chunks generated for document {document_id}. Skipping embedding and storage."
            )
            return []

        # Generate embeddings and add to ChromaDB
        try:
            # Note: ChromaDB's get_or_create_collection function takes an embedding_function
            # so it will handle embedding generation internally if a custom one is passed.
            # If default embedding_function is used, we need to generate embeddings here.
            # For now, let's rely on the collection's embedding_function if set.
            # If not, we'd do:
            # embeddings = [self.embedding_service.generate_embedding(c) for c in chunk_contents]
            # self.collection.add(
            #     documents=chunk_contents,
            #     embeddings=embeddings,
            #     metadatas=chunk_metadatas,
            #     ids=chunk_ids
            # )

            # Use ChromaDB's internal embedding function as specified during collection creation
            # (collection will initialize embedding function lazily if needed)
            self.collection.add(
                documents=chunk_contents, metadatas=chunk_metadatas, ids=chunk_ids
            )
            logger.info(
                f"Successfully ingested {len(chunk_ids)} chunks for document {document_id} into ChromaDB."
            )
            return chunk_ids
        except Exception as e:
            logger.error(f"Failed to ingest document {document_id} into ChromaDB: {e}")
            raise

    async def ingest_firestore_articles(self) -> int:
        """
        Fetches all articles from Firestore and ingests them into ChromaDB.
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
            f"Successfully ingested {ingested_count} Firestore articles into ChromaDB."
        )
        return ingested_count


# Global instance of the IngestionService
ingestion_service = IngestionService()
