"""
Web scraper service for fetching and processing content from government websites.
Converts scraped content to embeddings and stores in RAG vector store.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime, UTC
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from app.config import settings
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)


class WebScraperService:
    """Service for scraping government websites and ingesting content into RAG."""

    def __init__(self, timeout: int = 30, max_pages_per_site: int = 50):
        """
        Initialize web scraper service.
        
        Args:
            timeout: HTTP request timeout in seconds
            max_pages_per_site: Maximum pages to scrape per domain
        """
        self.timeout = timeout
        self.max_pages_per_site = max_pages_per_site
        self.session: Optional[httpx.AsyncClient] = None

    async def initialize(self):
        """Initialize async HTTP client."""
        if not self.session:
            self.session = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                verify=False  # For self-signed certs
            )
            logger.info("Web scraper service initialized")

    async def shutdown(self):
        """Cleanup async HTTP client."""
        if self.session:
            await self.session.aclose()
            self.session = None
            logger.info("Web scraper service shutdown")

    async def scrape_website(
        self,
        url: str,
        selector: Optional[str] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        """
        Scrape a single website and extract content.
        
        Args:
            url: Website URL to scrape
            selector: CSS selector to target specific content (e.g., "main", ".content")
            exclude_patterns: URL patterns to exclude (e.g., ["/admin", "/login"])
            
        Returns:
            Dict with page contents and metadata
        """
        if not self.session:
            await self.initialize()

        try:
            logger.info(f"Scraping website: {url}")
            
            visited_urls: Set[str] = set()
            pages: List[Dict[str, str]] = []
            
            # Start with the base URL
            to_visit = [url]
            domain = urlparse(url).netloc
            
            while to_visit and len(pages) < self.max_pages_per_site:
                current_url = to_visit.pop(0)
                
                # Skip if already visited
                if current_url in visited_urls:
                    continue
                    
                visited_urls.add(current_url)
                
                try:
                    # Fetch page
                    response = await self.session.get(current_url)
                    response.raise_for_status()
                    
                    # Parse HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract content
                    if selector:
                        content_elem = soup.select_one(selector)
                    else:
                        # Default: extract main content
                        content_elem = soup.find(['main', 'article']) or soup.body
                    
                    if content_elem:
                        text = content_elem.get_text(separator=' ', strip=True)
                        if len(text) > 100:  # Only include if substantial content
                            pages.append({
                                "url": current_url,
                                "title": soup.title.string if soup.title else "Untitled",
                                "content": text[:5000]  # Limit to 5000 chars per page
                            })
                            logger.debug(f"Scraped: {current_url} ({len(text)} chars)")
                    
                    # Extract links for crawling
                    for link in soup.find_all('a', href=True):
                        link_url = urljoin(current_url, link['href'])
                        link_domain = urlparse(link_url).netloc
                        
                        # Only follow links on same domain
                        if link_domain == domain and link_url not in visited_urls:
                            # Skip excluded patterns
                            if exclude_patterns:
                                if any(pattern in link_url for pattern in exclude_patterns):
                                    continue
                            
                            to_visit.append(link_url)
                    
                except Exception as e:
                    logger.warning(f"Failed to scrape {current_url}: {str(e)}")
                    continue
            
            logger.info(f"Scraped {len(pages)} pages from {url}")
            return {
                "url": url,
                "pages_count": len(pages),
                "pages": pages
            }
            
        except Exception as e:
            logger.error(f"Error scraping website {url}: {str(e)}")
            return {
                "url": url,
                "pages_count": 0,
                "pages": [],
                "error": str(e)
            }

    async def ingest_scraped_content(
        self,
        website_data: Dict,
        source_prefix: str = "web"
    ) -> Dict[str, int]:
        """
        Ingest scraped website content into RAG.
        
        Args:
            website_data: Output from scrape_website()
            source_prefix: Prefix for source identification
            
        Returns:
            Stats dict with ingestion counts
        """
        stats = {
            "total": len(website_data.get("pages", [])),
            "added": 0,
            "failed": 0
        }
        
        documents = []
        for page in website_data.get("pages", []):
            document = {
                "id": f"{source_prefix}_{hash(page['url']) % 10000}",
                "content": page["content"],
                "source": f"{source_prefix}:{page['url']}",
                "metadata": {
                    "url": page["url"],
                    "title": page["title"],
                    "scraped_at": datetime.now(UTC).isoformat(),
                    "type": "web_content"
                }
            }
            documents.append(document)
        
        if documents:
            try:
                result = await rag_service.add_documents(documents)
                stats["added"] = result.get("added", 0)
                stats["failed"] = result.get("failed", 0)
                logger.info(f"Ingested {stats['added']} documents from {website_data['url']}")
            except Exception as e:
                logger.error(f"Failed to ingest content: {str(e)}")
                stats["failed"] = len(documents)
        
        return stats

    async def scrape_and_ingest(
        self,
        url: str,
        selector: Optional[str] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Scrape a website and immediately ingest content.
        
        Args:
            url: Website URL to scrape
            selector: CSS selector for content extraction
            exclude_patterns: URL patterns to exclude
            
        Returns:
            Ingestion statistics
        """
        website_data = await self.scrape_website(
            url=url,
            selector=selector,
            exclude_patterns=exclude_patterns
        )
        
        stats = await self.ingest_scraped_content(website_data)
        return stats


# Global scraper instance
_web_scraper = None


def get_web_scraper() -> WebScraperService:
    """Get or initialize the web scraper service."""
    global _web_scraper
    if _web_scraper is None:
        _web_scraper = WebScraperService()
    return _web_scraper


async def initialize_web_scraper():
    """Initialize the web scraper service."""
    scraper = get_web_scraper()
    await scraper.initialize()


async def shutdown_web_scraper():
    """Shutdown the web scraper service."""
    scraper = get_web_scraper()
    await scraper.shutdown()
