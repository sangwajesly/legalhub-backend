"""
Comprehensive RAG Pipeline Test Script

Tests all components of the RAG system:
1. ChromaDB connection
2. Embedding service
3. PDF processor
4. Document ingestion
5. Document retrieval
6. RAG-augmented chat
"""

import sys
import asyncio
from datetime import datetime

print("=" * 60)
print("RAG PIPELINE COMPREHENSIVE TEST")
print("=" * 60)
print(f"Test started at: {datetime.now()}")
print()

# Test 1: ChromaDB Connection
print("[1/7] Testing ChromaDB Connection...")
try:
    from app.utils.vector_store import get_chroma_client
    client = get_chroma_client()
    print("✓ ChromaDB client initialized successfully")
    print(f"  Client type: {type(client)}")
except Exception as e:
    print(f"✗ ChromaDB connection failed: {e}")
    sys.exit(1)

# Test 2: Collection Creation
print("\n[2/7] Testing Collection Creation...")
try:
    from app.utils.vector_store import get_or_create_collection
    collection = get_or_create_collection("test_rag_collection", client=client)
    print(f"✓ Collection created: {collection.name}")
    print(f"  Collection count: {collection.count()}")
except Exception as e:
    print(f"✗ Collection creation failed: {e}")
    sys.exit(1)

# Test 3: Embedding Service
print("\n[3/7] Testing Embedding Service...")
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
    print("  Note: This may be due to model download in progress")

# Test 4: PDF Processor
print("\n[4/7] Testing PDF Processor...")
try:
    from app.services.pdf_processor import PDFProcessor
    processor = PDFProcessor()
    print("✓ PDF processor initialized")
    print(f"  Processor type: {type(processor)}")
except Exception as e:
    print(f"✗ PDF processor failed: {e}")

# Test 5: Document Ingestion
print("\n[5/7] Testing Document Ingestion...")
try:
    from app.services.rag_service import rag_service
    
    # Add test documents
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
    
    result = rag_service.add_documents(test_docs)
    print(f"✓ Documents ingested successfully")
    print(f"  Documents added: {result.get('added', 0)}")
    print(f"  Total in collection: {rag_service.collection.count()}")
except Exception as e:
    print(f"✗ Document ingestion failed: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Document Retrieval
print("\n[6/7] Testing Document Retrieval...")
try:
    query = "What are the elements of a valid contract?"
    results = rag_service.retrieve_documents(query, top_k=2)
    print(f"✓ Document retrieval working")
    print(f"  Query: '{query}'")
    print(f"  Results found: {len(results)}")
    if results:
        print(f"  Top result: {results[0].get('document', '')[:100]}...")
        print(f"  Similarity score: {results[0].get('score', 0):.4f}")
except Exception as e:
    print(f"✗ Document retrieval failed: {e}")
    import traceback
    traceback.print_exc()

# Test 7: RAG-Augmented Response
print("\n[7/7] Testing RAG-Augmented Response...")
try:
    async def test_rag_response():
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
        print(f"  Response preview: {response[:200]}...")
        return response, docs
    
    response, docs = asyncio.run(test_rag_response())
except Exception as e:
    print(f"✗ RAG-augmented response failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print("All core RAG components have been tested.")
print("Check the output above for any failures (✗)")
print(f"Test completed at: {datetime.now()}")
print("=" * 60)
