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
_EMBEDDING_DIMENSION = 768   # embedding-001 output dimension
_EMBEDDING_MODEL     = "models/embedding-001"

def _embed_texts(texts: List[str], task_type: str = "retrieval_document") -> List[List[float]]:
    """
    Embed a list of texts using Gemini text-embedding-004.
    task_type should be:
      - "retrieval_document"  during ingestion
      - "retrieval_query"     at query time
    """
    import google.generativeai as genai

    api_key = _GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Cannot generate embeddings."
        )
    genai.configure(api_key=api_key)

    embeddings = []
    for text in texts:
        result = genai.embed_content(
            model=_EMBEDDING_MODEL,
            content=text,
            task_type=task_type,
        )
        embeddings.append(result["embedding"])
    return embeddings


def _embed_query(query: str) -> List[float]:
    """Embed a single query string for similarity search."""
    return _embed_texts([query], task_type="retrieval_query")[0]


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

    def add_documents(self, documents: List[Dict[str, str]]) -> Dict[str, int]:
        """
        Embed and add documents using Gemini text-embedding-004.
        Each doc dict must have: id, content, source.
        """
        self._ensure_initialized()
        if not self.index:
            return {"added": 0, "total": len(self.documents)}

        texts = [doc["content"] for doc in documents]
        embeddings = _embed_texts(texts, task_type="retrieval_document")

        self.index.add(np.array(embeddings, dtype="float32"))
        self.documents.extend(documents)
        self._save_index()
        return {"added": len(documents), "total": len(self.documents)}

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Return the top_k most relevant chunks for a query."""
        self._ensure_initialized()
        if not self.index or not self.documents:
            return []

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
