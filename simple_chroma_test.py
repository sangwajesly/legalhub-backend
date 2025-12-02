"""
Simple test to check ChromaDB functionality
"""

import chromadb
from chromadb.utils import embedding_functions

def test_chroma_basic():
    """Test basic ChromaDB functionality"""
    print("Testing ChromaDB basic functionality...")

    try:
        # Try EphemeralClient first
        client = chromadb.EphemeralClient()
        print("✅ ChromaDB EphemeralClient created successfully")

        # Create a test collection
        collection = client.get_or_create_collection(
            name="test_collection",
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        )
        print("✅ Collection created with embedding function")

        # Add some test documents
        documents = [
            "This is a test document about legal matters.",
            "Criminal law deals with offenses against society.",
            "Contract law governs agreements between parties."
        ]

        collection.add(
            ids=["doc1", "doc2", "doc3"],
            documents=documents
        )
        print("✅ Documents added to collection")

        # Test search
        results = collection.query(
            query_texts=["What is criminal law?"],
            n_results=2
        )
        print("✅ Search query executed")
        print(f"   Found {len(results['documents'][0])} results")

        return True

    except Exception as e:
        print(f"❌ ChromaDB test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_chroma_basic()
    if success:
        print("🎉 ChromaDB basic test passed!")
    else:
        print("💥 ChromaDB basic test failed!")
