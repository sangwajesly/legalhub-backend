"""Pinecone remote vector store support for LegalHub.

This module provides a drop-in remote vector store implementation that
keeps the same public interface as the local FAISS store used by the app.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from app.config import settings
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class PineconeVectorStore:
    """Remote vector store implementation using Pinecone."""

    def __init__(self, collection_name: str = "legalhub_documents", dimension: int = 384):
        self.collection_name = collection_name
        self.dimension = dimension
        self.index = None
        self.embedding_service = EmbeddingService()
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return

        try:
            import pinecone
        except ImportError as exc:
            raise RuntimeError(
                "pinecone-client is required for remote vector storage. "
                "Install it with `pip install pinecone-client`."
            ) from exc

        api_key = settings.PINECONE_API_KEY or os.environ.get("PINECONE_API_KEY", "")
        environment = settings.PINECONE_ENVIRONMENT or os.environ.get("PINECONE_ENVIRONMENT", "")
        if not api_key or not environment:
            raise RuntimeError(
                "Pinecone configuration is missing. Set PINECONE_API_KEY and PINECONE_ENVIRONMENT."
            )

        pinecone.init(api_key=api_key, environment=environment)

        index_name = settings.PINECONE_INDEX_NAME or self.collection_name
        metric = settings.PINECONE_METRIC or "cosine"
        if index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=index_name,
                dimension=self.dimension,
                metric=metric,
            )

        self.index = pinecone.Index(index_name)
        self._initialized = True

    def _vector_metadata(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        metadata = {k: v for k, v in doc.items() if k != "content"}
        metadata["content"] = doc["content"]
        return metadata

    def add_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, int]:
        self._ensure_initialized()

        ids = [doc["id"] for doc in documents]
        existing = self.index.fetch(ids=ids)
        existing_ids = set(existing.vectors.keys()) if hasattr(existing, "vectors") else set()

        new_docs = [doc for doc in documents if doc["id"] not in existing_ids]
        if not new_docs:
            return {"added": 0, "total": self.count()}

        embeddings = [
            self.embedding_service.generate_embedding(doc["content"])
            for doc in new_docs
        ]
        upsert_payload = [
            (doc["id"], emb, self._vector_metadata(doc))
            for doc, emb in zip(new_docs, embeddings)
        ]

        self.index.upsert(vectors=upsert_payload)
        return {"added": len(new_docs), "total": self.count()}

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        self._ensure_initialized()
        if not query.strip():
            return []

        query_embedding = self.embedding_service.generate_embedding(query)
        response = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
        )

        matches = getattr(response, "matches", None) or response.get("matches", [])
        results: List[Dict[str, Any]] = []
        for match in matches:
            metadata = getattr(match, "metadata", None) or match.get("metadata", {})
            results.append(
                {
                    "id": getattr(match, "id", None) or match.get("id"),
                    "content": metadata.get("content", ""),
                    "source": metadata.get("source", "unknown"),
                    "metadata": metadata,
                    "score": 1.0 - float(getattr(match, "score", None) or match.get("score", 0)) / 2.0,
                    "distance": float(getattr(match, "score", None) or match.get("score", 0)),
                }
            )
        return results

    def count(self) -> int:
        self._ensure_initialized()
        stats = self.index.describe_index_stats()
        return int(stats.get("total_vector_count", 0))

    def reset(self):
        self._ensure_initialized()
        self.index.delete(delete_all=True)
        return True

    def document_ids_for_prefix(self, prefix: str) -> set[str]:
        # Remote store does not support fast prefix lookup by chunk id.
        # The ingestion flow will still work by deduping on exact ids in add_documents.
        return set()

    def has_document_prefix(self, prefix: str) -> bool:
        return False

    def sync_to_firebase(self) -> bool:
        logger.info("Pinecone backend does not sync via Firebase.")
        return False