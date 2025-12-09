"""
Comprehensive test script for RAG and AI Engine
Tests all components: FAISS store, embeddings, RAG service, Gemini integration
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.utils.faiss_store import get_vector_store
from app.services.rag_service import rag_service
from app.services.gemini_service import send_message
from app.services.langchain_service import generate_rag_response


async def test_faiss_store():
    """Test FAISS vector store initialization and basic operations"""
    print("\n" + "="*60)
    print("TEST 1: FAISS Vector Store")
    print("="*60)
    
    try:
        # Test initialization
        print("✓ Testing vector store initialization...")
        vector_store = get_vector_store()
        print(f"  - Collection: {vector_store.collection_name}")
        print(f"  - Dimension: {vector_store.dimension}")
        print(f"  - Current document count: {vector_store.count()}")
        
        # Test adding documents
        print("\n✓ Testing document addition...")
        test_docs = [
            {
                "id": "test_doc_1",
                "content": "A contract is a legally binding agreement between two or more parties. Essential elements include offer, acceptance, and consideration.",
                "source": "test_source"
            },
            {
                "id": "test_doc_2",
                "content": "Criminal law deals with offenses against society. Key concepts include actus reus (the act) and mens rea (criminal intent).",
                "source": "test_source"
            }
        ]
        
        result = vector_store.add_documents(test_docs)
        print(f"  - Added: {result['added']} documents")
        print(f"  - Total: {result['total']} documents")
        
        # Test search
        print("\n✓ Testing search functionality...")
        query = "What is a contract?"
        results = vector_store.search(query, top_k=2)
        print(f"  - Query: '{query}'")
        print(f"  - Results found: {len(results)}")
        
        for i, doc in enumerate(results, 1):
            print(f"  - Result {i}:")
            print(f"    Score: {doc.get('score', 0):.3f}")
            print(f"    ID: {doc.get('id', 'N/A')}")
            print(f"    Content preview: {doc.get('content', '')[:100]}...")
        
        print("\n✅ FAISS Vector Store: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ FAISS Vector Store: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_rag_service():
    """Test RAG service operations"""
    print("\n" + "="*60)
    print("TEST 2: RAG Service")
    print("="*60)
    
    try:
        # Test document retrieval
        print("✓ Testing document retrieval...")
        query = "criminal law"
        docs = await rag_service.retrieve_documents(query, top_k=2, score_threshold=0.1)
        print(f"  - Query: '{query}'")
        print(f"  - Documents retrieved: {len(docs)}")
        
        for i, doc in enumerate(docs, 1):
            print(f"  - Doc {i}: Score={doc.get('score', 0):.3f}, Source={doc.get('source', 'N/A')}")
        
        # Test prompt augmentation
        print("\n✓ Testing prompt augmentation...")
        user_query = "Explain criminal law"
        augmented = await rag_service.augment_prompt(user_query, docs, max_context_length=1000)
        print(f"  - Original query length: {len(user_query)} chars")
        print(f"  - Augmented prompt length: {len(augmented)} chars")
        print(f"  - Augmented prompt preview: {augmented[:200]}...")
        
        print("\n✅ RAG Service: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ RAG Service: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gemini_service():
    """Test Gemini AI service"""
    print("\n" + "="*60)
    print("TEST 3: Gemini AI Service")
    print("="*60)
    
    try:
        print(f"✓ Testing Gemini API connection...")
        print(f"  - Model: {settings.GEMINI_MODEL}")
        print(f"  - API Key configured: {'Yes' if settings.GOOGLE_API_KEY else 'No'}")
        print(f"  - Mock mode: {settings.DEBUG_MOCK_GEMINI}")
        
        test_prompt = "What is a contract? Answer in one sentence."
        print(f"\n✓ Sending test prompt: '{test_prompt}'")
        
        result = await send_message(test_prompt)
        
        if isinstance(result, dict):
            response = result.get("response", str(result))
            print(f"  - Response received: {len(response)} characters")
            print(f"  - Response preview: {response[:200]}...")
            
            if settings.DEBUG_MOCK_GEMINI:
                print("  - ⚠️  Using MOCK response (set DEBUG_MOCK_GEMINI=false for real API)")
            else:
                print("  - ✓ Using REAL Gemini API")
        else:
            print(f"  - Response: {result}")
        
        print("\n✅ Gemini AI Service: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Gemini AI Service: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_rag_integration():
    """Test full RAG + AI integration"""
    print("\n" + "="*60)
    print("TEST 4: RAG + AI Integration")
    print("="*60)
    
    try:
        print("✓ Testing end-to-end RAG response generation...")
        
        user_message = "What are the essential elements of a contract?"
        print(f"  - User query: '{user_message}'")
        
        response, retrieved_docs = await generate_rag_response(
            session_id=None,
            user_id="test_user",
            user_message=user_message,
            use_rag=True,
            top_k=2
        )
        
        print(f"  - Response generated: {len(response)} characters")
        print(f"  - Documents retrieved: {len(retrieved_docs)}")
        print(f"  - Response preview: {response[:300]}...")
        
        if retrieved_docs:
            print(f"\n  - Retrieved document sources:")
            for i, doc in enumerate(retrieved_docs[:2], 1):
                print(f"    {i}. Score: {doc.get('score', 0):.3f}, Source: {doc.get('source', 'N/A')}")
        
        print("\n✅ RAG + AI Integration: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ RAG + AI Integration: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_configuration():
    """Test configuration settings"""
    print("\n" + "="*60)
    print("TEST 0: Configuration Check")
    print("="*60)
    
    issues = []
    
    # Check CHROMADB_PATH
    if hasattr(settings, 'CHROMADB_PATH'):
        print(f"✓ CHROMADB_PATH: {settings.CHROMADB_PATH}")
        # Ensure directory exists
        os.makedirs(settings.CHROMADB_PATH, exist_ok=True)
    else:
        issues.append("CHROMADB_PATH not configured")
        print("❌ CHROMADB_PATH: MISSING")
    
    # Check Gemini settings
    if settings.GOOGLE_API_KEY:
        print(f"✓ GOOGLE_API_KEY: Configured")
    else:
        print("⚠️  GOOGLE_API_KEY: Not set (will use mock mode)")
    
    print(f"✓ GEMINI_MODEL: {settings.GEMINI_MODEL}")
    print(f"✓ DEBUG_MOCK_GEMINI: {settings.DEBUG_MOCK_GEMINI}")
    
    if issues:
        print(f"\n⚠️  Configuration issues found: {len(issues)}")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\n✅ Configuration: OK")
        return True


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("LEGALHUB RAG & AI ENGINE COMPREHENSIVE TEST")
    print("="*60)
    
    results = {}
    
    # Test 0: Configuration
    results['config'] = await test_configuration()
    
    if not results['config']:
        print("\n⚠️  Configuration issues detected. Some tests may fail.")
        print("   Please fix configuration before proceeding.\n")
    
    # Test 1: FAISS Store
    results['faiss'] = await test_faiss_store()
    
    # Test 2: RAG Service
    results['rag'] = await test_rag_service()
    
    # Test 3: Gemini Service
    results['gemini'] = await test_gemini_service()
    
    # Test 4: Full Integration
    if results['faiss'] and results['rag'] and results['gemini']:
        results['integration'] = await test_rag_integration()
    else:
        print("\n⚠️  Skipping integration test due to previous failures")
        results['integration'] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.upper():15} {status}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! RAG and AI engine are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

