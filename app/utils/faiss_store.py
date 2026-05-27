"""
FAISS Vector Store — Local / Git-committed persistence
=======================================================
Index files live in CHROMADB_PATH (default: ./chroma_db/).

These files are committed to Git, so:
  - Local dev (VS Code)  → loads from ./chroma_db/ instantly
  - Vercel deployment    → same files are in the deployed repo, same path

To update the index after adding new documents:
  1. Run:  uv run python scripts/ingest_pdfs_direct.py --reset
  2. Then: git add chroma_db/ && git commit -m "chore: update FAISS index" && git push
  Vercel will redeploy with the new index automatically.
"""

import logging
import os
import pickle
from typing import List, Optional, Any, Dict

logger = logging.getLogger(__name__)

# app.config is optional — falls back to env var or default path
try:
    from app.config import settings as _settings
    _CHROMADB_PATH = _settings.CHROMADB_PATH
except Exception:
    _CHROMADB_PATH = os.environ.get("CHROMADB_PATH", "./chroma_db")

# ---------------------------------------------------------------------------
# Heavy dependencies are imported LAZILY inside _ensure_initialized().
# This prevents Windows crashes from top-level sentence_transformers/jinja2 import.
# ---------------------------------------------------------------------------
FAISS_AVAILABLE = False
SENTENCE_TRANSFORMERS_AVAILABLE = False



# ---------------------------------------------------------------------------
# FAISSVectorStore
# ---------------------------------------------------------------------------

class FAISSVectorStore:
    """
    FAISS-based vector store backed by plain files on disk (committed to Git).

    Files are loaded from CHROMADB_PATH on first use (lazy init).
    Writes are saved back to the same directory immediately.

    Works identically in:
      - Local VS Code dev  (reads/writes ./chroma_db/)
      - Vercel serverless  (reads the git-committed ./chroma_db/ — read-only is fine
                            because Vercel only needs to *read* the index at runtime;
                            new ingestion is always done locally then pushed)
    """

    def __init__(self, collection_name: str = "legalhub_documents", dimension: int = 384):
        self.collection_name = collection_name
        self.dimension = dimension
        self.index = None
        self.documents: List[Dict] = []
        self.embedding_model = None
        self._initialized = False
        # Set by _ensure_initialized() — lazy-loaded to avoid Windows/jinja2 crash
        self._faiss = None
        self._np = None

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
    # Lazy initialisation
    # ------------------------------------------------------------------

    def _ensure_initialized(self):
        """Load model and index on first real operation."""
        if self._initialized:
            return

        # Lazy-import heavy deps here (not at module level) to avoid Windows crashes
        try:
            global FAISS_AVAILABLE, SENTENCE_TRANSFORMERS_AVAILABLE
            import faiss as _faiss
            import numpy as _np
            from sentence_transformers import SentenceTransformer as _ST
            FAISS_AVAILABLE = True
            SENTENCE_TRANSFORMERS_AVAILABLE = True
        except Exception as e:
            logger.warning(f"RAG dependencies unavailable: {e} — RAG disabled.")
            return

        logger.info("Initialising FAISS Vector Store…")
        try:
            if self.index is None:
                self.index = _faiss.IndexFlatL2(self.dimension)
            if self.embedding_model is None:
                self.embedding_model = _ST("all-MiniLM-L6-v2")
            # Store references for use in other methods
            self._faiss = _faiss
            self._np = _np
            self._load_index()
            self._initialized = True
            logger.info(f"FAISS ready — {len(self.documents)} chunks loaded.")
        except Exception as e:
            logger.error(f"Failed to initialise FAISS store: {e}")
            raise

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def _load_index(self):
        """Load existing index from disk if present."""
        idx_path = self._index_path()
        docs_path = self._docs_path()

        if os.path.exists(idx_path) and os.path.exists(docs_path):
            try:
                self.index = self._faiss.read_index(idx_path)
                with open(docs_path, "rb") as f:
                    self.documents = pickle.load(f)
                logger.info(
                    f"Loaded FAISS index: {len(self.documents)} chunks from {idx_path}"
                )
            except Exception as e:
                logger.warning(f"Could not read FAISS index from disk: {e}")
        else:
            logger.info(
                "No existing FAISS index found on disk — starting with an empty store."
            )

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def _save_index(self):
        """Persist index and documents to disk."""
        if not self.index:
            return
        try:
            self._faiss.write_index(self.index, self._index_path())
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
        Embed and add documents to the store.

        Each dict must have: id, content, source.
        Returns {added, total}.
        """
        self._ensure_initialized()

        if not self.index or not self.embedding_model:
            logger.warning("RAG dependencies missing — documents not added.")
            return {"added": 0, "total": len(self.documents)}

        texts = [doc["content"] for doc in documents]
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)

        self.index.add(self._np.array(embeddings, dtype="float32"))
        for doc in documents:
            self.documents.append(doc)

        self._save_index()
        return {"added": len(documents), "total": len(self.documents)}

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Return the top_k most relevant document chunks for query."""
        self._ensure_initialized()

        if not self.index or not self.embedding_model or not self.documents:
            return []

        q_emb = self.embedding_model.encode([query])
        distances, indices = self.index.search(
            self._np.array(q_emb, dtype="float32"),
            min(top_k, len(self.documents)),
        )

        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if 0 <= idx < len(self.documents):
                doc = self.documents[idx].copy()
                # L2 distance → cosine similarity (higher = more relevant)
                doc["score"] = max(0.0, 1.0 - float(dist) / 2.0)
                doc["distance"] = float(dist)
                doc["document"] = doc["content"]
                results.append(doc)

        return results

    def count(self) -> int:
        """Number of chunks currently in the store."""
        self._ensure_initialized()
        return len(self.documents)

    def reset(self):
        """Clear the store. Keeps the embedding model loaded so add_documents() works immediately after."""
        if not FAISS_AVAILABLE:
            return

        self._ensure_initialized()  # Load model + faiss refs first
        self.index = self._faiss.IndexFlatL2(self.dimension)
        self.documents = []
        self._initialized = True  # Keep model loaded, reset index only

        try:
            self._faiss.write_index(self.index, self._index_path())
            with open(self._docs_path(), "wb") as f:
                pickle.dump(self.documents, f)
            logger.info("FAISS index reset (empty).")
        except Exception as e:
            logger.warning(f"Could not write empty index during reset: {e}")

    def sync_to_firebase(self) -> bool:
        """
        Stub — Firebase Storage not used (requires paid plan).
        Returns False gracefully so callers don't crash.
        """
        logger.info(
            "sync_to_firebase() skipped — index is persisted via Git. "
            "Commit chroma_db/ after ingestion to update Vercel."
        )
        return False


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
_vector_store: Optional[FAISSVectorStore] = None


def get_vector_store(collection_name: str = "legalhub_documents") -> FAISSVectorStore:
    """Get (or create) the global FAISS vector store."""
    global _vector_store
    if _vector_store is None:
        _vector_store = FAISSVectorStore(collection_name)
    return _vector_store
