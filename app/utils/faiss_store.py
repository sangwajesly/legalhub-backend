"""
FAISS Vector Store with Hybrid Local + Firebase Storage Persistence
====================================================================
Load priority:
  1. Local disk  (fast, preferred for local VS Code dev)
  2. Firebase Storage  (cloud fallback for Vercel / CI / fresh installs)

Save behaviour:
  - Always saves to local disk immediately.
  - Uploads to Firebase Storage in the background (non-blocking).

This means:
  - Local dev: files already on disk → instant load, no download needed.
  - Vercel / fresh env: downloads from Firebase Storage on first request,
    caches to /tmp for the lifetime of the serverless container.
"""

import logging
import os
import pickle
import threading
from typing import List, Optional, Any, Dict

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional heavy dependencies (graceful degradation)
# ---------------------------------------------------------------------------
try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None
    np = None
    FAISS_AVAILABLE = False
    logger.warning("FAISS or numpy not installed. RAG features will be disabled.")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not installed. RAG features will be disabled.")

# ---------------------------------------------------------------------------
# Firebase Storage helper — lazy, so import errors don't crash the app
# ---------------------------------------------------------------------------

def _get_storage_bucket():
    """Return the Firebase Storage bucket, or None if unavailable."""
    try:
        from firebase_admin import storage
        bucket = storage.bucket()
        if bucket and bucket.name:
            return bucket
    except Exception as e:
        logger.debug(f"Firebase Storage not available: {e}")
    return None


def _upload_to_firebase(local_path: str, remote_path: str) -> bool:
    """Upload a local file to Firebase Storage. Returns True on success."""
    try:
        bucket = _get_storage_bucket()
        if not bucket:
            return False
        blob = bucket.blob(remote_path)
        blob.upload_from_filename(local_path)
        logger.info(f"Uploaded {local_path} → gs://{bucket.name}/{remote_path}")
        return True
    except Exception as e:
        logger.warning(f"Firebase Storage upload failed for {remote_path}: {e}")
        return False


def _download_from_firebase(remote_path: str, local_path: str) -> bool:
    """Download a file from Firebase Storage to a local path. Returns True on success."""
    try:
        bucket = _get_storage_bucket()
        if not bucket:
            return False
        blob = bucket.blob(remote_path)
        if not blob.exists():
            logger.info(f"Firebase Storage: {remote_path} does not exist yet.")
            return False
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        blob.download_to_filename(local_path)
        logger.info(f"Downloaded gs://{bucket.name}/{remote_path} → {local_path}")
        return True
    except Exception as e:
        logger.warning(f"Firebase Storage download failed for {remote_path}: {e}")
        return False


# ---------------------------------------------------------------------------
# FAISSVectorStore
# ---------------------------------------------------------------------------

class FAISSVectorStore:
    """
    FAISS-based vector store with hybrid local + Firebase Storage persistence.

    Local dev (VS Code):
        Files in CHROMADB_PATH are loaded instantly on startup.
        Uploads run in a background thread so they never block.

    Vercel / serverless:
        On first load, files are not present → downloads from Firebase Storage
        into /tmp (or CHROMADB_PATH) and caches for the container lifetime.
    """

    # Firebase Storage folder that holds index files
    FIREBASE_FOLDER = "faiss_index"

    def __init__(self, collection_name: str = "legalhub_documents", dimension: int = 384):
        self.collection_name = collection_name
        self.dimension = dimension
        self.index = None
        self.documents: List[Dict] = []
        self.embedding_model = None
        self._initialized = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _local_index_path(self) -> str:
        os.makedirs(settings.CHROMADB_PATH, exist_ok=True)
        return os.path.join(settings.CHROMADB_PATH, f"{self.collection_name}.faiss")

    def _local_docs_path(self) -> str:
        os.makedirs(settings.CHROMADB_PATH, exist_ok=True)
        return os.path.join(settings.CHROMADB_PATH, f"{self.collection_name}_docs.pkl")

    def _remote_index_path(self) -> str:
        return f"{self.FIREBASE_FOLDER}/{self.collection_name}.faiss"

    def _remote_docs_path(self) -> str:
        return f"{self.FIREBASE_FOLDER}/{self.collection_name}_docs.pkl"

    # ------------------------------------------------------------------
    # Lazy initialisation
    # ------------------------------------------------------------------

    def _ensure_initialized(self):
        """Lazy-load model and index (called on first real operation)."""
        if self._initialized:
            return

        if not FAISS_AVAILABLE or not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("FAISS / SentenceTransformer missing — RAG disabled.")
            return

        logger.info("Initialising FAISS Vector Store…")
        try:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            self._load_index()
            self._initialized = True
            logger.info(
                f"FAISS Vector Store ready: {len(self.documents)} chunks loaded."
            )
        except Exception as e:
            logger.error(f"Failed to initialise FAISS store: {e}")
            raise

    # ------------------------------------------------------------------
    # Load: local first, then Firebase Storage
    # ------------------------------------------------------------------

    def _load_index(self):
        """
        Load strategy:
          1. Try local disk — instant, preferred for local dev.
          2. If local files are missing, try Firebase Storage (Vercel path).
        """
        index_path = self._local_index_path()
        docs_path = self._local_docs_path()

        # --- Step 1: Local disk ---
        if os.path.exists(index_path) and os.path.exists(docs_path):
            try:
                self.index = faiss.read_index(index_path)
                with open(docs_path, "rb") as f:
                    self.documents = pickle.load(f)
                logger.info(
                    f"[LOCAL] Loaded FAISS index: {len(self.documents)} chunks "
                    f"from {index_path}"
                )
                return
            except Exception as e:
                logger.warning(f"Failed to read local FAISS index: {e}. Trying Firebase…")

        # --- Step 2: Firebase Storage fallback ---
        logger.info(
            "[FIREBASE] Local FAISS index not found. Attempting download from Firebase Storage…"
        )
        idx_ok = _download_from_firebase(self._remote_index_path(), index_path)
        docs_ok = _download_from_firebase(self._remote_docs_path(), docs_path)

        if idx_ok and docs_ok:
            try:
                self.index = faiss.read_index(index_path)
                with open(docs_path, "rb") as f:
                    self.documents = pickle.load(f)
                logger.info(
                    f"[FIREBASE] Loaded FAISS index: {len(self.documents)} chunks "
                    f"(downloaded from Firebase Storage)"
                )
                return
            except Exception as e:
                logger.warning(f"Failed to read downloaded FAISS index: {e}")

        # --- Nothing found anywhere — start fresh ---
        logger.info(
            "No existing FAISS index found locally or in Firebase Storage. "
            "Starting with an empty store."
        )

    # ------------------------------------------------------------------
    # Save: local + background Firebase upload
    # ------------------------------------------------------------------

    def _save_index(self):
        """
        Save to local disk immediately.
        Then kick off a background thread to upload to Firebase Storage.
        """
        if not self.index:
            return

        index_path = self._local_index_path()
        docs_path = self._local_docs_path()

        # 1. Local save (always, synchronous)
        try:
            faiss.write_index(self.index, index_path)
            with open(docs_path, "wb") as f:
                pickle.dump(self.documents, f)
            logger.debug(f"[LOCAL] Saved FAISS index ({len(self.documents)} chunks)")
        except Exception as e:
            logger.error(f"Failed to save FAISS index locally: {e}")
            return

        # 2. Firebase Storage upload (background, non-blocking)
        index_path_copy = index_path
        docs_path_copy = docs_path
        remote_index = self._remote_index_path()
        remote_docs = self._remote_docs_path()

        def _upload():
            try:
                _upload_to_firebase(index_path_copy, remote_index)
                _upload_to_firebase(docs_path_copy, remote_docs)
            except Exception as e:
                logger.debug(f"Background Firebase upload error: {e}")

        t = threading.Thread(target=_upload, daemon=True, name="faiss-firebase-upload")
        t.daemon = True
        t.start()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_documents(self, documents: List[Dict[str, str]]) -> Dict[str, int]:
        """
        Add documents to the vector store.

        Each document dict must have:
            id       – unique string identifier
            content  – text to embed
            source   – human-readable source label
        """
        self._ensure_initialized()

        if not self.index or not self.embedding_model:
            logger.warning("RAG dependencies missing. Documents not added.")
            return {"added": 0, "total": len(self.documents)}

        texts = [doc["content"] for doc in documents]
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)

        self.index.add(np.array(embeddings, dtype="float32"))
        for doc in documents:
            self.documents.append(doc)

        self._save_index()
        return {"added": len(documents), "total": len(self.documents)}

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for the most relevant documents for a query."""
        self._ensure_initialized()

        if not self.index or not self.embedding_model or len(self.documents) == 0:
            return []

        query_embedding = self.embedding_model.encode([query])
        distances, indices = self.index.search(
            np.array(query_embedding, dtype="float32"),
            min(top_k, len(self.documents)),
        )

        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if 0 <= idx < len(self.documents):
                doc = self.documents[idx].copy()
                # Convert L2 distance → cosine similarity (0–1, higher = more relevant)
                doc["score"] = max(0.0, 1.0 - float(distance) / 2.0)
                doc["distance"] = float(distance)
                doc["document"] = doc["content"]
                results.append(doc)

        return results

    def count(self) -> int:
        """Return number of chunks in the store."""
        self._ensure_initialized()
        return len(self.documents)

    def reset(self):
        """Clear all documents and the local index files."""
        if not FAISS_AVAILABLE:
            return
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        # Overwrite local files with empty index
        try:
            faiss.write_index(self.index, self._local_index_path())
            with open(self._local_docs_path(), "wb") as f:
                pickle.dump(self.documents, f)
        except Exception as e:
            logger.warning(f"Reset: could not clear local files: {e}")

    def sync_to_firebase(self) -> bool:
        """
        Manually trigger a synchronous upload of the current index to Firebase Storage.
        Useful after bulk ingestion to ensure Vercel gets the latest index immediately.
        Returns True if both files uploaded successfully.
        """
        index_path = self._local_index_path()
        docs_path = self._local_docs_path()

        if not os.path.exists(index_path) or not os.path.exists(docs_path):
            logger.warning("sync_to_firebase: no local index files to upload.")
            return False

        idx_ok = _upload_to_firebase(index_path, self._remote_index_path())
        docs_ok = _upload_to_firebase(docs_path, self._remote_docs_path())
        return idx_ok and docs_ok


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
_vector_store: Optional[FAISSVectorStore] = None


def get_vector_store(collection_name: str = "legalhub_documents") -> FAISSVectorStore:
    """Get or create the global FAISS vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = FAISSVectorStore(collection_name)
        logger.info(f"Global FAISS vector store created: '{collection_name}'")
    return _vector_store
