"""
Scheduled task for periodic web scraping and RAG ingestion.
Runs every 72 hours to fetch government websites and update embeddings.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.services.web_scraper import scrape_government_websites
from app.services.rag_service import rag_service
from app.services.pdf_ingestion_service import load_pdfs_from_folder
from app.config import settings
import os

logger = logging.getLogger(__name__)


class RAGScrapeScheduler:
    """Manages scheduled web scraping and RAG ingestion."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.last_run: Optional[datetime] = None
        self.last_run_status: str = "pending"
    
    async def scrape_and_ingest(self):
        """
        Scrape government websites and ingest into RAG.
        This is the main scheduled task.
        """
        try:
            logger.info("🕐 Starting scheduled web scrape and RAG ingestion...")
            self.last_run = datetime.now()
            self.last_run_status = "in_progress"
            
            # Scrape websites
            logger.info("📡 Scraping government websites...")
            documents = await scrape_government_websites()
            
            if not documents:
                logger.warning("No documents scraped from government websites")
                self.last_run_status = "no_documents"
                return
            
            logger.info(f"✓ Scraped {len(documents)} documents")
            
            # Ingest local PDFs
            logger.info("📂 Checking for local PDFs in data/pdfs...")
            pdf_path = os.path.join(os.getcwd(), "data", "pdfs")
            pdf_stats = await load_pdfs_from_folder(pdf_path)
            
            logger.info(f"✓ PDF Ingestion: {pdf_stats['success']} added")

            # Ingest into RAG (Web Documents)
            logger.info("🔄 Ingesting web documents into RAG vector store...")
            result = await rag_service.add_documents(documents)
            
            added = result.get("added", 0)
            skipped = result.get("skipped", 0)
            
            logger.info(f"✓ Web Ingestion complete: {added} added, {skipped} skipped")
            self.last_run_status = "success"
            
            # Log summary
            logger.info(f"""
╔════════════════════════════════════════╗
║  RAG Scrape & Ingest Job Completed     ║
╠════════════════════════════════════════╣
║ Timestamp: {self.last_run.isoformat()}
║ Websites Scraped: {len(documents)}
║ Web Docs Added: {added}
║ Local PDFs Added: {pdf_stats['success']}
║ Next Run: 72 hours from now
╚════════════════════════════════════════╝
            """)
            
        except Exception as e:
            logger.error(f"✗ Error during scrape and ingest: {str(e)}")
            self.last_run_status = f"error: {str(e)}"
            import traceback
            traceback.print_exc()
    
    def start(self, interval_hours: int = 72):
        """
        Start the scheduler.
        
        Args:
            interval_hours: Interval between runs in hours (default: 72)
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info(f"🚀 Starting RAG scheduler (runs every {interval_hours} hours)")
        
        # Add the scheduled job
        self.scheduler.add_job(
            self.scrape_and_ingest,
            trigger=IntervalTrigger(hours=interval_hours),
            id="rag_scrape_ingest",
            name="RAG Web Scrape & Ingest",
            replace_existing=True,
            max_instances=1  # Only one instance at a time
        )
        
        # Start the scheduler
        self.scheduler.start()
        self.is_running = True
        logger.info("✓ RAG scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        logger.info("Stopping RAG scheduler...")
        self.scheduler.shutdown()
        self.is_running = False
        logger.info("✓ RAG scheduler stopped")
    
    async def run_now(self):
        """Run the scrape and ingest task immediately."""
        logger.info("⚡ Running scrape and ingest NOW (manual trigger)")
        await self.scrape_and_ingest()
    
    def get_status(self) -> dict:
        """
        Get scheduler status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "is_running": self.is_running,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_run_status": self.last_run_status,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in self.scheduler.get_jobs()
            ]
        }


# Global scheduler instance
_scheduler_instance: Optional[RAGScrapeScheduler] = None


def get_rag_scheduler() -> RAGScrapeScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = RAGScrapeScheduler()
    return _scheduler_instance


async def initialize_scheduler():
    """Initialize and start the scheduler on app startup."""
    try:
        # Check if scraping is enabled
        if not settings.RAG_SCRAPE_ENABLED:
            logger.info("RAG scraping is disabled in settings")
            return
        
        scheduler = get_rag_scheduler()
        
        # Get interval from settings or use default 72 hours
        interval = settings.RAG_SCRAPE_INTERVAL_HOURS
        
        scheduler.start(interval_hours=interval)
        logger.info(f"✓ RAG scheduler initialized with {interval}h interval")
        
        # Optionally run immediately on startup
        if settings.RAG_SCRAPE_ON_STARTUP:
            logger.info("Running initial scrape on startup...")
            await scheduler.run_now()
    except Exception as e:
        logger.error(f"Failed to initialize RAG scheduler: {str(e)}")


def shutdown_scheduler():
    """Shutdown the scheduler on app shutdown."""
    scheduler = get_rag_scheduler()
    if scheduler.is_running:
        scheduler.stop()
        logger.info("✓ RAG scheduler shutdown")


if __name__ == "__main__":
    # Test the scheduler
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        scheduler = get_rag_scheduler()
        scheduler.start(interval_hours=72)
        
        # Simulate running for a short time
        try:
            await asyncio.sleep(5)
        finally:
            scheduler.stop()
    
    asyncio.run(test())
