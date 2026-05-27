"""Vector store selector for LegalHub.

Provides a single `get_vector_store()` entrypoint so the app can use
local FAISS by default and optionally switch to a hosted vector database.
"""

from app.config import settings
from app.utils.faiss_store import get_vector_store as get_faiss_vector_store
from app.utils.pinecone_store import PineconeVectorStore
import logging

logger = logging.getLogger(__name__)


def get_vector_store(collection_name: str = "legalhub_documents"):
    """Return the configured vector store implementation."""
    if settings.USE_REMOTE_VECTOR_STORE:
        store_type = settings.VECTOR_STORE_TYPE.lower().strip()
        if store_type == "local":
            return get_faiss_vector_store(collection_name)
        if store_type == "pinecone":
            try:
                return PineconeVectorStore(collection_name)
            except Exception as e:
                logger.warning(
                    "Failed to initialize Pinecone backend (%s). Falling back to local FAISS. Error: %s",
                    settings.PINECONE_INDEX_NAME,
                    e,
                )
                return get_faiss_vector_store(collection_name)
        raise RuntimeError(
            f"Remote vector store type '{settings.VECTOR_STORE_TYPE}' is not supported. "
            "Supported values: local, pinecone."
        )

    return get_faiss_vector_store(collection_name)
