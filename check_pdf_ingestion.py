"""
Check if PDFs from /data/pdfs are actually in FAISS and being used
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.utils.faiss_store import get_vector_store
from app.services.rag_service import rag_service
import asyncio


async def check_pdf_ingestion():
    """Check if PDFs are in FAISS and can be retrieved"""
    
    print("="*60)
    print("PDF INGESTION VERIFICATION")
    print("="*60)
    
    # 1. Check FAISS store
    print("\n1. Checking FAISS Vector Store...")
    vector_store = get_vector_store()
    doc_count = vector_store.count()
    print(f"   Total documents in FAISS: {doc_count}")
    
    if doc_count == 0:
        print("   ❌ NO DOCUMENTS FOUND IN FAISS!")
        print("   ⚠️  PDFs from /data/pdfs have NOT been ingested")
        return False
    
    # 2. Check for PDF sources
    print("\n2. Checking document sources...")
    pdf_docs = [doc for doc in vector_store.documents if 'pdf' in doc.get('source', '').lower()]
    print(f"   Documents with 'pdf' in source: {len(pdf_docs)}")
    
    if pdf_docs:
        print("   ✓ Found PDF documents:")
        for doc in pdf_docs[:5]:  # Show first 5
            source = doc.get('source', 'unknown')
            doc_id = doc.get('id', 'unknown')
            content_preview = doc.get('content', '')[:100]
            print(f"     - ID: {doc_id}")
            print(f"       Source: {source}")
            print(f"       Content preview: {content_preview}...")
    else:
        print("   ⚠️  No PDF documents found in FAISS")
    
    # 3. Test retrieval
    print("\n3. Testing document retrieval...")
    test_queries = [
        "penal code",
        "criminal law",
        "contract"
    ]
    
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        docs = await rag_service.retrieve_documents(query, top_k=3, score_threshold=0.1)
        print(f"   Retrieved: {len(docs)} documents")
        
        if docs:
            for i, doc in enumerate(docs[:2], 1):
                score = doc.get('score', 0)
                source = doc.get('source', 'unknown')
                print(f"     {i}. Score: {score:.3f}, Source: {source}")
                if 'pdf' in source.lower():
                    print(f"        ✓ This is from a PDF!")
        else:
            print(f"     ⚠️  No documents retrieved for this query")
    
    # 4. Check if Penal Code PDF is there
    print("\n4. Checking for Penal-Code-eng.pdf...")
    penal_code_docs = [
        doc for doc in vector_store.documents 
        if 'penal' in doc.get('source', '').lower() or 'penal' in doc.get('id', '').lower()
    ]
    
    if penal_code_docs:
        print(f"   ✓ Found {len(penal_code_docs)} documents related to Penal Code")
        for doc in penal_code_docs[:3]:
            print(f"     - {doc.get('id', 'unknown')}: {doc.get('source', 'unknown')}")
    else:
        print("   ❌ Penal Code PDF NOT found in FAISS")
        print("   ⚠️  The PDF in /data/pdfs/Penal-Code-eng.pdf has NOT been ingested")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if doc_count == 0:
        print("❌ CRITICAL: FAISS store is EMPTY")
        print("   → PDFs have NOT been ingested")
        print("   → Run: python scripts/batch_load_pdfs.py")
        return False
    elif len(pdf_docs) == 0:
        print("⚠️  WARNING: No PDF documents found in FAISS")
        print("   → PDFs may not have been ingested correctly")
        print("   → Run: python scripts/batch_load_pdfs.py")
        return False
    else:
        print(f"✅ SUCCESS: Found {len(pdf_docs)} PDF documents in FAISS")
        print("   → PDFs are available for RAG queries")
        return True


if __name__ == "__main__":
    result = asyncio.run(check_pdf_ingestion())
    sys.exit(0 if result else 1)

