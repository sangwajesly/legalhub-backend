"""
Scheduler service for managing periodic RAG update jobs.
Handles 72-hour web scraping cycles and other scheduled tasks.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Callable
from datetime import datetime, UTC, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.services.web_scraper_service import get_web_scraper

logger = logging.getLogger(__name__)


class RAGScheduler:
    """Manages scheduled jobs for RAG system updates."""

    def __init__(self):
        """Initialize RAG scheduler."""
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.is_running = False
        self.government_websites: List[Dict] = []
        self.last_run_times: Dict[str, datetime] = {}

    async def initialize(self):
        """Initialize and start the scheduler."""
        try:
            if self.scheduler is None:
                self.scheduler = AsyncIOScheduler()
                
                # Load government websites from config
                self._load_government_websites()
                
                # Schedule the web scraping job
                if settings.RAG_ENABLE_SCHEDULER and self.government_websites:
                    self.scheduler.add_job(
                        self._scrape_government_sites,
                        IntervalTrigger(hours=72),
                        id="scrape_gov_sites",
                        name="Scrape government websites every 72 hours",
                        misfire_grace_time=3600,
                        max_instances=1
                    )
                    logger.info("Scheduled government website scraping job (72 hours)")
                
                # Start the scheduler
                if not self.scheduler.running:
                    self.scheduler.start()
                    self.is_running = True
                    logger.info("RAG scheduler started")
                    
        except Exception as e:
            logger.error(f"Failed to initialize RAG scheduler: {str(e)}")
            raise

    async def shutdown(self):
        """Shutdown the scheduler."""
        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown()
                self.is_running = False
                logger.info("RAG scheduler shutdown")
        except Exception as e:
            logger.error(f"Error during scheduler shutdown: {str(e)}")

    def _load_government_websites(self):
        """Load government websites from configuration."""
        # Default government websites for legal information
        default_websites = [
            {
                "name": "Ministry of Justice",
                "url": "https://www.justice.gov",
                "selector": "main, article, .content",
                "exclude_patterns": ["/admin", "/login", "/internal"]
            },
            {
                "name": "Parliament/Legislature",
                "url": "https://www.parliament.gov",
                "selector": "main, .legislation",
                "exclude_patterns": ["/admin"]
            },
            {
                "name": "Court System",
                "url": "https://www.courts.gov",
                "selector": "main, .decisions",
                "exclude_patterns": ["/admin"]
            }
        ]
        
        # Allow custom websites from config/env
        custom_websites = getattr(settings, 'RAG_GOVERNMENT_WEBSITES', [])
        
        self.government_websites = custom_websites or default_websites
        logger.info(f"Loaded {len(self.government_websites)} government websites")

    async def _scrape_government_sites(self):
        """Scrape all configured government websites."""
        logger.info("Starting government website scraping job")
        scraper = get_web_scraper()
        
        stats = {
            "total_sites": len(self.government_websites),
            "successful": 0,
            "failed": 0,
            "total_documents_added": 0,
            "started_at": datetime.now(UTC).isoformat(),
            "details": []
        }
        
        for site in self.government_websites:
            try:
                logger.info(f"Scraping: {site['name']} ({site['url']})")
                
                result = await scraper.scrape_and_ingest(
                    url=site["url"],
                    selector=site.get("selector"),
                    exclude_patterns=site.get("exclude_patterns")
                )
                
                stats["details"].append({
                    "site": site["name"],
                    "url": site["url"],
                    "status": "success",
                    "documents_added": result.get("added", 0)
                })
                
                stats["successful"] += 1
                stats["total_documents_added"] += result.get("added", 0)
                self.last_run_times[site["url"]] = datetime.now(UTC)
                
            except Exception as e:
                logger.error(f"Failed to scrape {site['name']}: {str(e)}")
                stats["failed"] += 1
                stats["details"].append({
                    "site": site["name"],
                    "url": site["url"],
                    "status": "failed",
                    "error": str(e)
                })
        
        stats["completed_at"] = datetime.now(UTC).isoformat()
        logger.info(f"Government website scraping job completed: {stats}")
        
        return stats

    async def scrape_single_site(self, site_url: str) -> Dict:
        """
        Manually trigger scraping for a single government site.
        
        Args:
            site_url: URL of the site to scrape
            
        Returns:
            Scraping and ingestion statistics
        """
        logger.info(f"Manually scraping site: {site_url}")
        
        # Find matching site config
        site_config = next(
            (s for s in self.government_websites if s["url"] == site_url),
            {
                "name": site_url,
                "url": site_url,
                "selector": None,
                "exclude_patterns": None
            }
        )
        
        scraper = get_web_scraper()
        result = await scraper.scrape_and_ingest(
            url=site_url,
            selector=site_config.get("selector"),
            exclude_patterns=site_config.get("exclude_patterns")
        )
        
        self.last_run_times[site_url] = datetime.now(UTC)
        return result

    def add_government_website(
        self,
        name: str,
        url: str,
        selector: Optional[str] = None,
        exclude_patterns: Optional[List[str]] = None
    ):
        """
        Add a new government website to scraping list.
        
        Args:
            name: Name of the government site
            url: Base URL of the site
            selector: CSS selector for content extraction
            exclude_patterns: URL patterns to exclude
        """
        site = {
            "name": name,
            "url": url,
            "selector": selector or "main, article, .content",
            "exclude_patterns": exclude_patterns or ["/admin", "/login"]
        }
        
        # Check if already exists
        if not any(s["url"] == url for s in self.government_websites):
            self.government_websites.append(site)
            logger.info(f"Added government website: {name} ({url})")
        else:
            logger.warning(f"Website already exists: {url}")

    def get_status(self) -> Dict:
        """Get current scheduler status."""
        return {
            "is_running": self.is_running,
            "scheduler_running": self.scheduler.running if self.scheduler else False,
            "total_government_sites": len(self.government_websites),
            "government_sites": [
                {
                    "name": s["name"],
                    "url": s["url"],
                    "last_scraped": self.last_run_times.get(s["url"], "Never").isoformat()
                    if isinstance(self.last_run_times.get(s["url"]), datetime)
                    else self.last_run_times.get(s["url"], "Never")
                }
                for s in self.government_websites
            ],
            "next_run": self._get_next_run_time()
        }

    def _get_next_run_time(self) -> Optional[str]:
        """Get the next scheduled run time."""
        if self.scheduler and self.scheduler.running:
            job = self.scheduler.get_job("scrape_gov_sites")
            if job:
                next_run = job.next_run_time
                return next_run.isoformat() if next_run else None
        return None


# Global scheduler instance
_rag_scheduler = None


def get_rag_scheduler() -> RAGScheduler:
    """Get or initialize the RAG scheduler."""
    global _rag_scheduler
    if _rag_scheduler is None:
        _rag_scheduler = RAGScheduler()
    return _rag_scheduler


async def initialize_rag_scheduler():
    """Initialize the RAG scheduler."""
    scheduler = get_rag_scheduler()
    await scheduler.initialize()


async def shutdown_rag_scheduler():
    """Shutdown the RAG scheduler."""
    scheduler = get_rag_scheduler()
    await scheduler.shutdown()
