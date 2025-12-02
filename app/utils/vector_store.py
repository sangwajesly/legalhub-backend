"""
Utility functions for initializing and interacting with ChromaDB.
"""

import chromadb
from chromadb.utils import embedding_functions
from app.config import settings
from typing import Optional


_sentence_transformer_ef = None


def get_sentence_transformer_ef(model_name: str = "all-MiniLM-L6-v2"):
    """Lazily initialize and return a SentenceTransformer embedding function."""
    global _sentence_transformer_ef
    if _sentence_transformer_ef is None:
        _sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )
    return _sentence_transformer_ef


def get_chroma_client(path: Optional[str] = None) -> chromadb.Client:
    """
    Returns a persistent ChromaDB client.

    Args:
        path: Optional path to the ChromaDB directory. If None, uses settings.CHROMADB_PATH.

    Returns:
        A ChromaDB client instance.
    """
    if path is None:
        path = settings.CHROMADB_PATH

    # Ensure the directory exists
    # import os
    # os.makedirs(path, exist_ok=True)

    # For a persistent client, specify the path to the directory where data will be stored
    client = chromadb.PersistentClient(path=path)
    return client


def get_or_create_collection(
    collection_name: str,
    client: Optional[chromadb.Client] = None,
    embedding_function=None,
) -> chromadb.Collection:
    """
    Gets an existing ChromaDB collection or creates a new one if it doesn't exist.

    Args:
        collection_name: The name of the collection.
        client: Optional ChromaDB client. If None, a new client is obtained.
        embedding_function: The embedding function to use for the collection.

    Returns:
        A ChromaDB Collection instance.
    """
    if client is None:
        client = get_chroma_client()

    # If no embedding_function provided, lazily obtain the sentence-transformer ef
    if embedding_function is None:
        embedding_function = get_sentence_transformer_ef()

    # Get or create the collection
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
    )
    return collection
