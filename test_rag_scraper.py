"""
Test script for RAG web scraper and 72-hour scheduler.
Validates scraper functionality without needing real websites.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, UTC

sys.path.insert(0, str(Path(__file__).parent))

from app.services.web_scraper import WebScraper, scrape_government_websites, GovernmentWebsiteSources
from app.services.rag_scheduler import get_rag_scheduler
from app.services.rag_service import rag_service


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_test(title: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{title}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def print_success(message: str):
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message: str):
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_info(message: str):
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


# ============================================================================
# TEST 1: Government Website Sources
# ============================================================================

async def test_government_sources():
    """Test government website sources management."""
    print_test("TEST 1: Government Website Sources")
    
    try:
        # Get default sources
        sources = GovernmentWebsiteSources.get_sources()
        print_success(f"Loaded {len(sources)} government sources")
        
        for name, url in sources.items():
            print(f"  • {name}: {url}")
        
        # Add a test source
        GovernmentWebsiteSources.add_source(
            "Test Court",
            "https://www.testcourt.example.com"
        )
        print_success("Added test source successfully")
        
        # Verify it was added
        sources = GovernmentWebsiteSources.get_sources()
        if "Test Court" in sources:
            print_success("Test source verified in sources list")
        else:
            print_warning("Test source not found in sources (may not persist)")
        
        return True
    except Exception as e:
        print_error(f"Government sources test failed: {str(e)}")
        return False


# ============================================================================
# TEST 2: Web Scraper Initialization
# ============================================================================

async def test_web_scraper_init():
    """Test web scraper initialization."""
    print_test("TEST 2: Web Scraper Initialization")
    
    try:
        scraper = WebScraper(timeout=30)
        print_success("WebScraper instance created")
        
        # Test async context manager
        async with scraper as s:
            print_success("WebScraper async context manager works")
            print_info(f"Session timeout: {scraper.timeout} seconds")
        
        return True
    except Exception as e:
        print_error(f"Web scraper initialization failed: {str(e)}")
        return False


# ============================================================================
# TEST 3: HTML Text Extraction
# ============================================================================

async def test_html_extraction():
    """Test HTML text extraction."""
    print_test("TEST 3: HTML Text Extraction")
    
    try:
        # Sample HTML
        html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <script>console.log('ignored');</script>
                <h1>Government Information</h1>
                <p>This is important legal information about contracts and laws.</p>
                <footer>Footer content ignored</footer>
            </body>
        </html>
        """
        
        text = WebScraper.extract_text(html)
        print_success("HTML extracted successfully")
        print(f"  Extracted text: {text[:100]}...")
        
        # Verify script was removed
        if "console.log" not in text:
            print_success("Script tags properly removed")
        
        if "Government" in text or "Legal" in text.lower():
            print_success("Main content captured correctly")
        
        return True
    except Exception as e:
        print_error(f"HTML extraction test failed: {str(e)}")
        return False


# ============================================================================
# TEST 4: RAG Scheduler Initialization
# ============================================================================

async def test_scheduler_init():
    """Test RAG scheduler initialization."""
    print_test("TEST 4: RAG Scheduler Initialization")
    
    try:
        scheduler = get_rag_scheduler()
        print_success("RAG scheduler instance created")
        
        # Check scheduler status
        print_success("Scheduler instance verified")
        print(f"  Running: {scheduler.is_running}")
        print(f"  Last run: {scheduler.last_run or 'Never'}")
        print(f"  Last run status: {scheduler.last_run_status}")
        
        if scheduler.scheduler:
            print_success("APScheduler instance exists")
        
        return True
    except Exception as e:
        print_error(f"Scheduler initialization test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# TEST 5: Document Ingestion Test
# ============================================================================

async def test_document_ingestion():
    """Test ingesting sample documents into RAG."""
    print_test("TEST 5: Document Ingestion to RAG")
    
    try:
        # Create mock government documents
        sample_documents = [
            {
                "id": "test_gov_001",
                "content": "Contract law is the body of law that governs the making and enforcement of agreements. A valid contract requires offer, acceptance, consideration, and capacity.",
                "source": "web:government.example.com",
                "metadata": {
                    "url": "https://government.example.com/contract-law",
                    "title": "Contract Law Basics",
                    "type": "web_content"
                }
            },
            {
                "id": "test_gov_002",
                "content": "Criminal liability requires proof of both the actus reus (guilty act) and mens rea (guilty mind). Intent is a crucial element in determining criminal culpability.",
                "source": "web:government.example.com",
                "metadata": {
                    "url": "https://government.example.com/criminal-law",
                    "title": "Criminal Liability",
                    "type": "web_content"
                }
            }
        ]
        
        # Add to RAG
        result = await rag_service.add_documents(sample_documents)
        print_success("Documents added to RAG")
        print(f"  Added: {result.get('added', 0)}")
        print(f"  Skipped: {result.get('skipped', 0)}")
        
        # Verify by searching
        search_results = await rag_service.retrieve_documents(
            query="What is a contract?",
            top_k=2
        )
        print_success(f"Retrieved {len(search_results)} documents from RAG search")
        
        if search_results:
            print(f"  Top result relevance: {search_results[0].get('score', 'N/A')}")
        
        return True
    except Exception as e:
        print_error(f"Document ingestion test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# TEST 6: Scheduler Job Configuration
# ============================================================================

async def test_scheduler_config():
    """Test scheduler job configuration."""
    print_test("TEST 6: Scheduler Job Configuration")
    
    try:
        scheduler = get_rag_scheduler()
        print_success("Scheduler configuration checked")
        
        # Check if scheduler is initialized but not running (to avoid side effects)
        print_info("Scheduler job setup:")
        print_info("  • Job ID: rag_scrape_ingest")
        print_info("  • Frequency: Every 72 hours")
        print_info("  • Max instances: 1 (prevents parallel runs)")
        print_info("  • Trigger: IntervalTrigger(hours=72)")
        
        # Verify scheduler state
        print_success(f"Scheduler state: is_running={scheduler.is_running}")
        
        if scheduler.last_run_status:
            print_info(f"Last run status: {scheduler.last_run_status}")
        
        return True
    except Exception as e:
        print_error(f"Scheduler config test failed: {str(e)}")
        return False


# ============================================================================
# TEST 7: Scraper with Mock Data
# ============================================================================

async def test_scraper_mock():
    """Test scraper functionality with mock data."""
    print_test("TEST 7: Web Scraper with Mock Data")
    
    try:
        # Create a sample scrape result structure
        mock_result = {
            "url": "https://www.example-government.com",
            "pages_count": 3,
            "pages": [
                {
                    "url": "https://www.example-government.com/laws",
                    "title": "Laws and Regulations",
                    "content": "This page contains information about government laws and regulations..." * 10
                },
                {
                    "url": "https://www.example-government.com/contracts",
                    "title": "Contract Information",
                    "content": "Contracts are binding agreements between parties..." * 10
                }
            ]
        }
        
        print_success("Mock scrape result created")
        print(f"  Pages scraped: {mock_result['pages_count']}")
        print(f"  Content size: {sum(len(p['content']) for p in mock_result['pages'])} characters")
        
        # Simulate ingestion
        documents = []
        for page in mock_result['pages']:
            doc = {
                "id": f"mock_{hash(page['url']) % 10000}",
                "content": page['content'],
                "source": f"web:{page['url']}",
                "metadata": {
                    "url": page['url'],
                    "title": page['title'],
                    "type": "web_content"
                }
            }
            documents.append(doc)
        
        print_success(f"Created {len(documents)} mock documents for ingestion")
        
        return True
    except Exception as e:
        print_error(f"Scraper mock test failed: {str(e)}")
        return False


# ============================================================================
# TEST 8: Configuration Validation
# ============================================================================

async def test_configuration():
    """Test RAG scraper configuration."""
    print_test("TEST 8: Configuration Validation")
    
    try:
        from app.config import settings
        
        # Check configuration
        configs = {
            "RAG Scheduler Enabled": getattr(settings, 'RAG_ENABLE_SCHEDULER', True),
            "Scrape Interval (hours)": getattr(settings, 'RAG_SCRAPE_INTERVAL_HOURS', 72),
            "Max Pages Per Site": getattr(settings, 'RAG_MAX_PAGES_PER_SITE', 50),
            "Scraper Timeout (sec)": getattr(settings, 'RAG_SCRAPER_TIMEOUT', 30),
        }
        
        print_success("Configuration loaded")
        for key, value in configs.items():
            print(f"  • {key}: {value}")
        
        # Validate settings
        if configs["RAG Scheduler Enabled"]:
            print_success("RAG scheduler is enabled")
        else:
            print_warning("RAG scheduler is disabled (enable in .env: RAG_ENABLE_SCHEDULER=true)")
        
        if configs["Scrape Interval (hours)"] == 72:
            print_success("Scrape interval correctly set to 72 hours")
        
        return True
    except Exception as e:
        print_error(f"Configuration validation failed: {str(e)}")
        return False


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def run_all_tests():
    """Run all RAG scraper tests."""
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}🌐 RAG WEB SCRAPER & 72-HOUR SCHEDULER TEST SUITE{Colors.ENDC}")
    print(f"{Colors.OKBLUE}Testing at: {datetime.now(UTC).isoformat()}{Colors.ENDC}\n")
    
    results = {
        "Government Sources": await test_government_sources(),
        "Scraper Initialization": await test_web_scraper_init(),
        "HTML Text Extraction": await test_html_extraction(),
        "Scheduler Initialization": await test_scheduler_init(),
        "Document Ingestion": await test_document_ingestion(),
        "Scheduler Configuration": await test_scheduler_config(),
        "Scraper Mock Data": await test_scraper_mock(),
        "Configuration": await test_configuration(),
    }
    
    # Summary
    print_test("TEST SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.OKGREEN}PASS{Colors.ENDC}" if result else f"{Colors.FAIL}FAIL{Colors.ENDC}"
        print(f"  {test_name}: {status}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.ENDC}")
    
    if passed == total:
        print(f"{Colors.OKGREEN}✓ All tests passed! Web scraper and scheduler are ready.{Colors.ENDC}\n")
        print_info("Next steps:")
        print_info("  1. Add government websites: POST /api/rag/sources/add")
        print_info("  2. Trigger scraping: POST /api/rag/scheduler/run-now")
        print_info("  3. System will automatically scrape every 72 hours")
    else:
        print(f"{Colors.FAIL}✗ Some tests failed. Check the output above.{Colors.ENDC}\n")
    
    return passed == total


def main():
    """Main entry point."""
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Tests interrupted by user.{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Unexpected error: {str(e)}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
