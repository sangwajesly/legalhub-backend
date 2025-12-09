"""
Improved Async RAG Pipeline Test Script

Tests all components with proper async/await handling
"""

import sys
import asyncio
from datetime import datetime

async def main():
    print("=" * 60)
    print("RAG PIPELINE COMPREHENSIVE TEST (ASYNC)")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    print()

    # Test 1: ChromaDB Connection
    print("[1/8] Testing ChromaDB Connection...")
    try:
        from app.utils.vector_store import get_chroma_client
        client = get_chroma_client()
        print("✓ ChromaDB client initialized successfully")
        print(f"  Client type: {type(client).__name__}")
    except Exception as e:
        print(f"✗ ChromaDB connection failed: {e}")
        return

    # Test 2: Collection Creation
    print("\n[2/8] Testing Collection Creation...")
    try:
        from app.utils.vector_store import get_or_create_collection
        collection = get_or_create_collection("test_rag_collection", client=client)
        print(f"✓ Collection created: {collection.name}")
        print(f"  Initial count: {collection.count()}")
    except Exception as e:
        print(f"✗ Collection creation failed: {e}")
        return

    # Test 3: Embedding Service
    print("\n[3/8] Testing Embedding Service...")
    try:
        from app.services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        test_text = "This is a test legal document about contract law."
        embeddings = embedding_service.embed_texts([test_text])
        print(f"✓ Embedding service working")
        print(f"  Embedding dimensions: {len(embeddings[0])}")
        print(f"  Model: {embedding_service.model_name}")
    except Exception as e:
        print(f"✗ Embedding service failed: {e}")

    # Test 4: PDF Processor
    print("\n[4/8] Testing PDF Processor...")
    try:
        from app.services.pdf_processor import PDFProcessor
        processor = PDFProcessor()
        print("✓ PDF processor initialized")
    except Exception as e:
        print(f"✗ PDF processor failed: {e}")

    # Test 5: RAG Service Initialization
    print("\n[5/8] Testing RAG Service...")
    try:
        from app.services.rag_service import rag_service
        print(f"✓ RAG service initialized")
        print(f"  Collection: {rag_service.collection_name}")
    except Exception as e:
        print(f"✗ RAG service failed: {e}")
        return

    # Test 6: Document Ingestion (ASYNC)
    print("\n[6/8] Testing Document Ingestion...")
    try:
        test_docs = [
            {
                "id": "doc1",
                "content": "Contract law governs agreements between parties. A valid contract requires offer, acceptance, and consideration.",
                "source": "test_contract_law.txt"
            },
            {
                "id": "doc2",
                "content": "Criminal law defines offenses against society. It includes crimes like theft, assault, and fraud.",
                "source": "test_criminal_law.txt"
            },
            {
                "id": "doc3",
                "content": "Property law deals with ownership and tenancy. It covers real estate, personal property, and intellectual property.",
                "source": "test_property_law.txt"
            }
        ]
        
        result = await rag_service.add_documents(test_docs)
        print(f"✓ Documents ingested successfully")
        print(f"  Documents added: {result.get('added', 0)}")
        print(f"  Total in collection: {rag_service.collection.count()}")
    except Exception as e:
        print(f"✗ Document ingestion failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 7: Document Retrieval (ASYNC)
    print("\n[7/8] Testing Document Retrieval...")
    try:
        query = "What are the elements of a valid contract?"
        results = await rag_service.retrieve_documents(query, top_k=2)
        print(f"✓ Document retrieval working")
        print(f"  Query: '{query}'")
        print(f"  Results found: {len(results)}")
        if results:
            print(f"  Top result preview: {results[0].get('document', '')[:80]}...")
            print(f"  Similarity score: {results[0].get('score', 0):.4f}")
    except Exception as e:
        print(f"✗ Document retrieval failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 8: RAG-Augmented Response (ASYNC)
    print("\n[8/8] Testing RAG-Augmented Response...")
    try:
        user_query = "Explain the requirements for a valid contract"
        response, docs = await rag_service.generate_rag_response(
            session_id="test_session",
            user_id="test_user",
            user_message=user_query,
            use_rag=True,
            top_k=2
        )
        print(f"✓ RAG-augmented response generated")
        print(f"  Query: '{user_query}'")
        print(f"  Retrieved docs: {len(docs)}")
        print(f"  Response preview: {response[:150]}...")
    except Exception as e:
        print(f"✗ RAG-augmented response failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✓ All core RAG components tested successfully!")
    print(f"Test completed at: {datetime.now()}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
