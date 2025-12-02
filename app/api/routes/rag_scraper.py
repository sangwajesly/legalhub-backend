"""
API endpoints for RAG scheduler and web scraper management.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional, Dict, List

from app.dependencies import get_current_user
from app.services.rag_scheduler import get_rag_scheduler
from app.services.web_scraper import GovernmentWebsiteSources, scrape_government_websites
from app.services.rag_service import rag_service

router = APIRouter(prefix="/api/rag", tags=["RAG Scraper"])


# ============================================================================
# Scheduler Management Endpoints
# ============================================================================

@router.get("/scheduler/status")
async def get_scheduler_status(user: Optional[dict] = Depends(get_current_user)):
    """
    Get the current status of the RAG scheduler.
    
    Returns:
        - is_running: Whether the scheduler is running
        - last_run: Timestamp of last run
        - last_run_status: Status of last run
        - jobs: List of scheduled jobs
    """
    scheduler = get_rag_scheduler()
    return scheduler.get_status()


@router.post("/scheduler/run-now")
async def run_scraper_now(user: Optional[dict] = Depends(get_current_user)):
    """
    Trigger the web scraper and RAG ingestion immediately.
    Does not affect the regular 72-hour schedule.
    """
    try:
        scheduler = get_rag_scheduler()
        await scheduler.run_now()
        return {
            "status": "success",
            "message": "Web scraper triggered successfully",
            "timestamp": scheduler.last_run.isoformat() if scheduler.last_run else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running scraper: {str(e)}"
        )


# ============================================================================
# Website Sources Management Endpoints
# ============================================================================

@router.get("/sources")
async def get_sources(user: Optional[dict] = Depends(get_current_user)):
    """
    Get all configured government website sources.
    
    Returns:
        List of sources with their URLs
    """
    sources = GovernmentWebsiteSources.get_sources()
    return {
        "count": len(sources),
        "sources": [
            {
                "name": name,
                "url": url
            }
            for name, url in sources.items()
        ]
    }


@router.post("/sources/add")
async def add_source(
    name: str,
    url: str,
    user: Optional[dict] = Depends(get_current_user)
):
    """
    Add a new government website source.
    
    Args:
        name: Display name for the source
        url: URL to scrape
    """
    try:
        # Validate URL format
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        
        GovernmentWebsiteSources.add_source(name, url)
        return {
            "status": "success",
            "message": f"Added source: {name}",
            "source": {"name": name, "url": url}
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error adding source: {str(e)}"
        )


@router.delete("/sources/{source_name}")
async def remove_source(
    source_name: str,
    user: Optional[dict] = Depends(get_current_user)
):
    """
    Remove a government website source.
    
    Args:
        source_name: Name of the source to remove
    """
    try:
        GovernmentWebsiteSources.remove_source(source_name)
        return {
            "status": "success",
            "message": f"Removed source: {source_name}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error removing source: {str(e)}"
        )


@router.put("/sources/update")
async def update_sources(
    sources: Dict[str, str],
    user: Optional[dict] = Depends(get_current_user)
):
    """
    Update multiple government website sources at once.
    
    Args:
        sources: Dictionary of source_name -> url mappings
    """
    try:
        GovernmentWebsiteSources.update_sources(sources)
        return {
            "status": "success",
            "message": f"Updated {len(sources)} sources",
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating sources: {str(e)}"
        )


# ============================================================================
# Manual Scraping Endpoints
# ============================================================================

@router.post("/scrape-now")
async def scrape_now(
    sources: Optional[Dict[str, str]] = None,
    user: Optional[dict] = Depends(get_current_user)
):
    """
    Manually scrape websites and get results without saving to RAG.
    Useful for testing and validation.
    
    Args:
        sources: Optional custom sources to scrape (uses all configured if not provided)
    
    Returns:
        List of scraped documents with content
    """
    try:
        documents = await scrape_government_websites(custom_sources=sources)
        
        return {
            "status": "success",
            "count": len(documents),
            "documents": [
                {
                    "id": doc["id"],
                    "source": doc["source"],
                    "url": doc.get("url"),
                    "char_count": doc["metadata"].get("char_count", 0),
                    "preview": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"]
                }
                for doc in documents
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scraping websites: {str(e)}"
        )


@router.post("/scrape-and-ingest")
async def scrape_and_ingest(
    sources: Optional[Dict[str, str]] = None,
    user: Optional[dict] = Depends(get_current_user)
):
    """
    Manually scrape websites and ingest into RAG immediately.
    
    Args:
        sources: Optional custom sources to scrape (uses all configured if not provided)
    
    Returns:
        Status of ingestion with document counts
    """
    try:
        # Scrape
        documents = await scrape_government_websites(custom_sources=sources)
        
        if not documents:
            return {
                "status": "warning",
                "message": "No documents scraped",
                "added": 0,
                "skipped": 0
            }
        
        # Ingest into RAG
        result = await rag_service.add_documents(documents)
        
        return {
            "status": "success",
            "message": "Documents scraped and ingested successfully",
            "documents_scraped": len(documents),
            "documents_added": result.get("added", 0),
            "documents_skipped": result.get("skipped", 0),
            "timestamp": None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scraping and ingesting: {str(e)}"
        )
