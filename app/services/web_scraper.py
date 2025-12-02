"""
Web scraper for government websites.
Fetches and processes content from legal/government sources.
"""

import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebScraper:
    """Scrapes content from websites and extracts relevant legal information."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the web scraper.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch content from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if fetch fails
        """
        if not self.session:
            raise RuntimeError("WebScraper must be used as async context manager")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            async with self.session.get(url, headers=headers, ssl=False) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Failed to fetch {url}: Status {response.status}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    @staticmethod
    def extract_text(html: str, remove_scripts: bool = True) -> str:
        """
        Extract text content from HTML.
        
        Args:
            html: HTML content
            remove_scripts: Whether to remove script/style tags
            
        Returns:
            Extracted text
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style tags
            if remove_scripts:
                for script in soup(["script", "style"]):
                    script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {str(e)}")
            return ""
    
    async def scrape_website(
        self,
        url: str,
        max_depth: int = 1,
        follow_links: bool = False
    ) -> Dict[str, str]:
        """
        Scrape a website and extract content.
        
        Args:
            url: Starting URL
            max_depth: Maximum depth for link following
            follow_links: Whether to follow internal links
            
        Returns:
            Dictionary with 'content' and 'source' keys
        """
        content = await self.fetch_url(url)
        if not content:
            return {"content": "", "source": url}
        
        text = self.extract_text(content)
        
        if not text:
            logger.warning(f"No text extracted from {url}")
            return {"content": "", "source": url}
        
        # Limit content size (50KB per page)
        if len(text) > 50000:
            text = text[:50000] + "\n[Content truncated...]"
        
        return {
            "content": text,
            "source": url,
            "extracted_at": datetime.now().isoformat(),
            "char_count": len(text)
        }


class GovernmentWebsiteSources:
    """Collection of government websites to scrape."""
    
    # Legal and government sources
    SOURCES = {
        # African legal resources
        "African Legal Support Facility": "https://www.alsf.int/",
        "ECOWAS Court": "https://www.courtecowas.justice.org/",
        "Pan African Parliament": "https://www.parl.org.au/",
        
        # International legal resources
        "UN Treaties": "https://treaties.un.org/",
        "International Court of Justice": "https://www.icj-cij.org/",
        
        # Government websites (generic - user can customize)
        "Legal Information": "https://www.google.com/search?q=legal+documents",
        
        # Note: Add specific country government sites here
        # Example: "Cameroon Justice": "https://www.justice.gov.cm/",
    }
    
    @classmethod
    def get_sources(cls) -> Dict[str, str]:
        """Get all configured sources."""
        return cls.SOURCES.copy()
    
    @classmethod
    def add_source(cls, name: str, url: str):
        """Add a new source."""
        cls.SOURCES[name] = url
        logger.info(f"Added source: {name} -> {url}")
    
    @classmethod
    def remove_source(cls, name: str):
        """Remove a source."""
        if name in cls.SOURCES:
            del cls.SOURCES[name]
            logger.info(f"Removed source: {name}")
    
    @classmethod
    def update_sources(cls, sources_dict: Dict[str, str]):
        """Update multiple sources."""
        cls.SOURCES.update(sources_dict)
        logger.info(f"Updated {len(sources_dict)} sources")


async def scrape_government_websites(
    custom_sources: Optional[Dict[str, str]] = None,
    follow_links: bool = False
) -> List[Dict[str, str]]:
    """
    Scrape all configured government websites.
    
    Args:
        custom_sources: Optional custom sources to override defaults
        follow_links: Whether to follow internal links
        
    Returns:
        List of scraped documents
    """
    sources = custom_sources or GovernmentWebsiteSources.get_sources()
    
    logger.info(f"Starting scrape of {len(sources)} websites")
    documents = []
    
    async with WebScraper() as scraper:
        tasks = [
            scraper.scrape_website(url, follow_links=follow_links)
            for name, url in sources.items()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for (name, url), result in zip(sources.items(), results):
            if isinstance(result, Exception):
                logger.error(f"Error scraping {name}: {str(result)}")
                continue
            
            if result.get("content"):
                doc = {
                    "id": f"gov_{urlparse(url).netloc.replace('.', '_')}_{int(datetime.now().timestamp())}",
                    "content": result["content"],
                    "source": f"government_website:{name}",
                    "url": url,
                    "metadata": {
                        "source_name": name,
                        "url": url,
                        "scraped_at": datetime.now().isoformat(),
                        "char_count": result.get("char_count", 0)
                    }
                }
                documents.append(doc)
                logger.info(f"Scraped {name}: {result.get('char_count', 0)} characters")
            else:
                logger.warning(f"No content extracted from {name}")
    
    logger.info(f"Successfully scraped {len(documents)} documents")
    return documents


if __name__ == "__main__":
    # Test the scraper
    async def test():
        docs = await scrape_government_websites()
        print(f"Scraped {len(docs)} documents")
        for doc in docs:
            print(f"- {doc['metadata']['source_name']}: {doc['metadata']['char_count']} chars")
    
    asyncio.run(test())
