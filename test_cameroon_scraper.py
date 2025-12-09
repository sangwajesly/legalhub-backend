"""
Test script for Cameroon Government Web Scraper & RAG Integration
"""
import asyncio
import logging
from app.services.web_scraper import scrape_government_websites
from app.services.rag_service import rag_service
from app.utils.faiss_store import get_vector_store

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_scraper_integration():
    print("\n🇨🇲 TESTING CAMEROON GOVERNMENT SCRAPER & RAG PIPELINE 🇨🇲")
    print("=========================================================")
    
    # 1. Run Scraper
    print("\n1. Starting Web Scraper...")
    custom_sources = {
        "Presidency of Cameroon": "https://www.prc.cm/en",
        "Ministry of Justice": "http://www.minjustice.gov.cm"
    }
    
    documents = await scrape_government_websites(custom_sources=custom_sources)
    
    if not documents:
        print("❌ Failed to scrape any documents. Check network or URLs.")
        return
        
    print(f"\n✅ Scraped {len(documents)} documents successfully!")
    for doc in documents:
        print(f"   - {doc['metadata']['source_name']}: {doc['metadata']['char_count']} chars")
        print(f"     URL: {doc['url']}")
        print(f"     Preview: {doc['content'][:100].replace(chr(10), ' ')}...")
        
    # 2. Ingest into RAG
    print("\n2. Ingesting into RAG (FAISS)...")
    result = await rag_service.add_documents(documents)
    
    print(f"✅ Ingestion Result: {result}")
    
    # 3. Verify Vector Store
    print("\n3. Verifying Vector Store State...")
    store = get_vector_store()
    count = store.count()
    print(f"✅ Total documents in FAISS index: {count}")
    
    # 4. Search Verification
    print("\n4. Testing Search on New Content...")
    query = "President Paul Biya statements"  # Likely to match Presidency content
    results = await rag_service.retrieve_documents(query, top_k=2)
    
    if results:
        print(f"✅ Search returned {len(results)} results for '{query}'")
        for res in results:
            print(f"   - Score: {res['score']:.4f}")
            print(f"     Source: {res['metadata'].get('source_name')}")
            print(f"     Snippet: {res['content'][:150]}...")
    else:
        print("⚠️ Search returned no results (might be expected if content differs)")

if __name__ == "__main__":
    asyncio.run(test_scraper_integration())
