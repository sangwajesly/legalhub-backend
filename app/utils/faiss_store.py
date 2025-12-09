"""
FAISS-based vector store implementation (replacing ChromaDB)

FAISS (Facebook AI Similarity Search) is simpler and has no C++ build issues on Windows.
"""

import faiss
import numpy as np
import pickle
import os
from typing import Optional, List, Dict, Any
from sentence_transformers import SentenceTransformer
from app.config import settings


class FAISSVectorStore:
    """Simple FAISS-based vector store for RAG"""
    
    def __init__(self, collection_name: str = "legalhub_documents", dimension: int = 384):
        self.collection_name = collection_name
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)  # L2 distance
        self.documents = []  # Store document metadata
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Try to load existing index
        self._load_index()
    
    def _get_index_path(self):
        """Get path for saving/loading index"""
        os.makedirs(settings.CHROMADB_PATH, exist_ok=True)
        return os.path.join(settings.CHROMADB_PATH, f"{self.collection_name}.faiss")
    
    def _get_docs_path(self):
        """Get path for saving/loading documents"""
        os.makedirs(settings.CHROMADB_PATH, exist_ok=True)
        return os.path.join(settings.CHROMADB_PATH, f"{self.collection_name}_docs.pkl")
    
    def _load_index(self):
        """Load existing index and documents if they exist"""
        index_path = self._get_index_path()
        docs_path = self._get_docs_path()
        
        if os.path.exists(index_path) and os.path.exists(docs_path):
            try:
                self.index = faiss.read_index(index_path)
                with open(docs_path, 'rb') as f:
                    self.documents = pickle.load(f)
                print(f"Loaded existing FAISS index with {len(self.documents)} documents")
            except Exception as e:
                print(f"Could not load existing index: {e}")
    
    def _save_index(self):
        """Save index and documents to disk"""
        try:
            faiss.write_index(self.index, self._get_index_path())
            with open(self._get_docs_path(), 'wb') as f:
                pickle.dump(self.documents, f)
        except Exception as e:
            print(f"Could not save index: {e}")
    
    def add_documents(self, documents: List[Dict[str, str]]) -> Dict[str, int]:
        """
        Add documents to the vector store
        
        Args:
            documents: List of dicts with 'id', 'content', 'source'
        
        Returns:
            Dict with count of added documents
        """
        texts = [doc['content'] for doc in documents]
        embeddings = self.embedding_model.encode(texts)
        
        # Add to FAISS index
        self.index.add(np.array(embeddings).astype('float32'))
        
        # Store document metadata
        for doc in documents:
            self.documents.append(doc)
        
        # Save to disk
        self._save_index()
        
        return {"added": len(documents), "total": len(self.documents)}
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of documents with scores
        """
        if len(self.documents) == 0:
            return []
        
        # Encode query
        query_embedding = self.embedding_model.encode([query])
        
        # Search FAISS index
        distances, indices = self.index.search(
            np.array(query_embedding).astype('float32'), 
            min(top_k, len(self.documents))
        )
        
        # Convert distances to similarity scores (lower distance = higher similarity)
        # Normalize to 0-1 range
        max_distance = distances[0].max() if len(distances[0]) > 0 else 1.0
        
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                # Convert L2 distance to similarity score (0-1, higher is better)
                doc['score'] = 1.0 - (distance / (max_distance + 1e-6))
                doc['document'] = doc['content']
                results.append(doc)
        
        return results
    
    def count(self) -> int:
        """Get number of documents in the store"""
        return len(self.documents)
    
    def reset(self):
        """Clear all documents"""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        self._save_index()


# Global instance
_vector_store = None


def get_vector_store(collection_name: str = "legalhub_documents") -> FAISSVectorStore:
    """Get or create the global vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = FAISSVectorStore(collection_name)
        print(f"Initialized FAISS vector store: {collection_name}")
    return _vector_store
