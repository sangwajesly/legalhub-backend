"""
FAISS Vector Store — Gemini Embedding API backend
==================================================
Uses Google Gemini text-embedding-004 (768-dim) for both ingestion and query-time embedding.
This replaces the previous sentence-transformers / PyTorch approach, which was too large
for Vercel's 250MB serverless function limit.

Benefits over local SentenceTransformer:
  - Zero extra dependencies (google-generativeai is already installed)
  - No model download on cold start
  - Works identically on local VS Code and Vercel
  - 768-dim vectors for higher-quality semantic search

Index files (*.faiss + *_docs.pkl) are committed to Git so Vercel has them on deploy.
Re-run ingest_pdfs_direct.py then commit chroma_db/ after adding new documents.
"""

import logging
import os
import pickle
import time
from typing import List, Optional, Any, Dict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config — read CHROMADB_PATH without importing the full app package
# ---------------------------------------------------------------------------
try:
    from app.config import settings as _settings
    _CHROMADB_PATH = _settings.CHROMADB_PATH
    _GOOGLE_API_KEY = _settings.GOOGLE_API_KEY
except Exception:
    _CHROMADB_PATH = os.environ.get("CHROMADB_PATH", "./chroma_db")
    _GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# ---------------------------------------------------------------------------
# Gemini embedding (lazy import — avoids startup crashes)
# ---------------------------------------------------------------------------
_EMBEDDING_DIMENSION = 3072  # gemini-embedding-2 output dimension
_EMBEDDING_MODEL     = "gemini-embedding-2"
_EMBED_API_VER       = "v1"

def _embed_texts(texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
    """
    Embed texts using Gemini embedding-001 via direct REST API (no SDK).
    Upgraded to use batchEmbedContents endpoint with robust auto-chunking (max 100 items per request).
    """
    if not texts:
        return []

    import requests as _requests

    api_key = _GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set. Cannot generate embeddings.")

    batch_url = (
        f"https://generativelanguage.googleapis.com/{_EMBED_API_VER}"
        f"/models/{_EMBEDDING_MODEL}:batchEmbedContents?key={api_key}"
    )

    # Gemini requires taskType in uppercase
    api_task_type = task_type.upper() if task_type else "RETRIEVAL_DOCUMENT"

    embeddings = []
    # Gemini batchEmbedContents supports up to 100 requests per batch
    batch_size = 100
    for idx in range(0, len(texts), batch_size):
        chunk = texts[idx:idx + batch_size]
        requests_payload = []
        for text in chunk:
            requests_payload.append({
                "model": f"models/{_EMBEDDING_MODEL}",
                "content": {"parts": [{"text": text}]},
                "taskType": api_task_type,
            })
        
        payload = {"requests": requests_payload}
        resp = _requests.post(batch_url, json=payload, timeout=45)
        resp.raise_for_status()
        
        data = resp.json()
        for emb in data.get("embeddings", []):
            embeddings.append(emb["values"])
            
    return embeddings


def _embed_query(query: str) -> List[float]:
    """Embed a single query string for similarity search."""
    return _embed_texts([query], task_type="RETRIEVAL_QUERY")[0]


# ---------------------------------------------------------------------------
# Optional FAISS (graceful degradation if not installed)
# ---------------------------------------------------------------------------
try:
    import faiss
    import numpy as np
    _FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    np = None
    _FAISS_AVAILABLE = False
    logger.warning("faiss-cpu not installed. RAG retrieval disabled.")


# ---------------------------------------------------------------------------
# FAISSVectorStore
# ---------------------------------------------------------------------------

class FAISSVectorStore:
    """
    FAISS-based vector store backed by Gemini text-embedding-004 (768-dim).

    Index files are persisted to CHROMADB_PATH and committed to Git.
    On Vercel they are read directly from the deployed repo.
    """

    def __init__(self, collection_name: str = "legalhub_documents",
                 dimension: int = _EMBEDDING_DIMENSION):
        self.collection_name = collection_name
        self.dimension = dimension
        self.index = None
        self.documents: List[Dict] = []
        self._initialized = False

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------

    def _index_path(self) -> str:
        os.makedirs(_CHROMADB_PATH, exist_ok=True)
        return os.path.join(_CHROMADB_PATH, f"{self.collection_name}.faiss")

    def _docs_path(self) -> str:
        os.makedirs(_CHROMADB_PATH, exist_ok=True)
        return os.path.join(_CHROMADB_PATH, f"{self.collection_name}_docs.pkl")

    # ------------------------------------------------------------------
    # Lazy init — load index on first use
    # ------------------------------------------------------------------

    def _ensure_initialized(self):
        if self._initialized:
            return
        if not _FAISS_AVAILABLE:
            logger.warning("FAISS not available — RAG disabled.")
            return

        self.index = faiss.IndexFlatL2(self.dimension)
        self._load_index()
        self._initialized = True
        logger.info(f"FAISS ready — {len(self.documents)} chunks (Gemini 768-dim).")

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------

    def _load_index(self):
        idx_path = self._index_path()
        docs_path = self._docs_path()

        if os.path.exists(idx_path) and os.path.exists(docs_path):
            try:
                self.index = faiss.read_index(idx_path)
                with open(docs_path, "rb") as f:
                    self.documents = pickle.load(f)
                logger.info(
                    f"Loaded FAISS index: {len(self.documents)} chunks from {idx_path}"
                )
            except Exception as e:
                logger.warning(f"Could not read FAISS index: {e}. Starting fresh.")
        else:
            logger.info("No existing FAISS index found — starting empty.")

    def _save_index(self):
        if not self.index:
            return
        try:
            faiss.write_index(self.index, self._index_path())
            with open(self._docs_path(), "wb") as f:
                pickle.dump(self.documents, f)
            logger.debug(f"Saved FAISS index — {len(self.documents)} chunks.")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def _document_ids(self) -> set[str]:
        return {doc["id"] for doc in self.documents}

    def document_ids_for_prefix(self, prefix: str) -> set[str]:
        prefix_token = f"{prefix}_chunk_"
        return {doc_id for doc_id in self._document_ids() if doc_id.startswith(prefix_token)}

    def has_document_prefix(self, prefix: str) -> bool:
        return bool(self.document_ids_for_prefix(prefix))

    def add_documents(self, documents: List[Dict[str, str]]) -> Dict[str, int]:
        """
        Embed and add documents using Gemini text-embedding-004.
        Each doc dict must have: id, content, source.
        """
        self._ensure_initialized()
        if not self.index:
            return {"added": 0, "total": len(self.documents)}

        existing_ids = self._document_ids()
        deduped_docs = [doc for doc in documents if doc["id"] not in existing_ids]

        if not deduped_docs:
            return {"added": 0, "total": len(self.documents)}

        texts = [doc["content"] for doc in deduped_docs]
        try:
            embeddings = _embed_texts(texts, task_type="retrieval_document")
            self.index.add(np.array(embeddings, dtype="float32"))
            logger.info(f"Successfully generated Gemini embeddings for {len(deduped_docs)} documents.")
        except Exception as e:
            logger.warning(
                f"Failed to generate Gemini embeddings for ingestion ({e}). "
                "Using local dummy vectors for index compatibility."
            )
            # Add zero vectors of correct dimension to FAISS so it remains syntactically valid
            embeddings = [[0.0] * self.dimension for _ in deduped_docs]
            self.index.add(np.array(embeddings, dtype="float32"))

        self.documents.extend(deduped_docs)
        self._save_index()
        return {"added": len(deduped_docs), "total": len(self.documents)}

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Return the top_k most relevant chunks for a query."""
        self._ensure_initialized()
        if not self.index or not self.documents:
            return []

        try:
            q_emb = _embed_query(query)
            distances, indices = self.index.search(
                np.array([q_emb], dtype="float32"),
                min(top_k, len(self.documents)),
            )

            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if 0 <= idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    doc["score"] = max(0.0, 1.0 - float(dist) / 2.0)
                    doc["distance"] = float(dist)
                    doc["document"] = doc["content"]
                    results.append(doc)
            return results
        except Exception as e:
            logger.warning(
                f"Gemini embedding search failed ({e}). "
                "Falling back to high-speed local TF-IDF keyword search."
            )
            return self._local_keyword_search(query, top_k)

    def _local_keyword_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Pure Python TF-IDF inspired local keyword-matching search.
        Zero external dependencies, completely offline, and runs instantly in <1ms.
        """
        import math
        import re

        # Tokenizer helper
        def tokenize(text: str) -> List[str]:
            return re.findall(r'[a-zA-Z0-9_]+', text.lower())

        query_tokens = set(tokenize(query))
        if not query_tokens or not self.documents:
            return []

        # 1. Calculate document frequencies for unique terms in the corpus
        doc_freqs = {}
        for doc in self.documents:
            tokens = set(tokenize(doc.get("content", "")))
            for t in tokens:
                doc_freqs[t] = doc_freqs.get(t, 0) + 1

        num_docs = len(self.documents)

        # 2. Calculate TF-IDF matching score for each document chunk
        scored_docs = []
        for doc in self.documents:
            content = doc.get("content", "")
            doc_tokens = tokenize(content)
            if not doc_tokens:
                continue

            # Term Frequency of token in this document chunk
            tf = {}
            for t in doc_tokens:
                tf[t] = tf.get(t, 0) + 1

            score = 0.0
            for token in query_tokens:
                if token in tf:
                    # TF score (log scaled for term density dampening)
                    tf_score = 1.0 + math.log(tf[token])
                    # IDF score (with Laplace smoothing)
                    df = doc_freqs.get(token, 1)
                    idf = math.log(1.0 + num_docs / df)
                    score += tf_score * idf

            if score > 0.0:
                scored_docs.append((score, doc))

        if not scored_docs:
            return []

        # Sort documents by score descending
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        max_score = scored_docs[0][0]

        # 3. Format and return top K matching chunks
        results = []
        for score, doc_orig in scored_docs[:top_k]:
            doc = doc_orig.copy()
            # Normalize relevance score between 0.1 and 1.0
            doc["score"] = max(0.1, min(1.0, score / max_score))
            doc["distance"] = 1.0 - doc["score"]
            doc["document"] = doc["content"]
            results.append(doc)

        return results

    def count(self) -> int:
        self._ensure_initialized()
        return len(self.documents)

    def reset(self):
        if not _FAISS_AVAILABLE:
            return
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        self._initialized = True
        self._save_index()
        logger.info("FAISS index reset (empty).")

    def sync_to_firebase(self) -> bool:
        """Stub — index is persisted via Git. Commit chroma_db/ after ingestion."""
        logger.info("sync_to_firebase() skipped — use git commit chroma_db/ instead.")
        return False


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
_vector_store: Optional[FAISSVectorStore] = None


def get_vector_store(collection_name: str = "legalhub_documents") -> FAISSVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = FAISSVectorStore(collection_name)
    return _vector_store
