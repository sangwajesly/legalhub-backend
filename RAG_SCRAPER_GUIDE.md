# RAG Web Scraper & Scheduler Guide

## Overview

LegalHub now includes an automated web scraper that periodically fetches content from government and legal websites, converts them to embeddings, and adds them to the RAG (Retrieval-Augmented Generation) vector store. This keeps your knowledge base updated with the latest legal information automatically.

---

## Quick Start

### Default Behavior
- **Runs automatically every 72 hours** after app startup
- Fetches content from configured government websites
- Converts content to embeddings
- Adds to RAG vector store for semantic search

### Manual Trigger
```bash
# Run scraper immediately (doesn't affect 72-hour schedule)
curl -X POST http://localhost:8000/api/rag/scheduler/run-now \
  -H "Authorization: Bearer TOKEN"
```

---

## Configuration

### Environment Variables (in `.env`)

```env
# Enable/disable automatic scraping
RAG_SCRAPE_ENABLED=true

# Interval between scrapes (in hours)
RAG_SCRAPE_INTERVAL_HOURS=72

# Run scraper immediately on startup
RAG_SCRAPE_ON_STARTUP=false
```

### Configuration Examples

**Production Setup:**
```env
RAG_SCRAPE_ENABLED=true
RAG_SCRAPE_INTERVAL_HOURS=72  # 3 days
RAG_SCRAPE_ON_STARTUP=false   # Don't run on startup
```

**Development Setup:**
```env
RAG_SCRAPE_ENABLED=true
RAG_SCRAPE_INTERVAL_HOURS=24  # Daily for testing
RAG_SCRAPE_ON_STARTUP=true    # Test on startup
```

**Disabled (Manual Only):**
```env
RAG_SCRAPE_ENABLED=false
```

---

## API Endpoints

### 1. Get Scheduler Status

```bash
curl -X GET http://localhost:8000/api/rag/scheduler/status \
  -H "Authorization: Bearer TOKEN"
```

**Response:**
```json
{
  "is_running": true,
  "last_run": "2025-12-02T14:35:00",
  "last_run_status": "success",
  "jobs": [
    {
      "id": "rag_scrape_ingest",
      "name": "RAG Web Scrape & Ingest",
      "next_run_time": "2025-12-05T14:35:00"
    }
  ]
}
```

### 2. Trigger Scraper Now

```bash
curl -X POST http://localhost:8000/api/rag/scheduler/run-now \
  -H "Authorization: Bearer TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "message": "Web scraper triggered successfully",
  "timestamp": "2025-12-02T14:35:00"
}
```

---

## Website Sources Management

### 3. Get All Configured Sources

```bash
curl -X GET http://localhost:8000/api/rag/sources \
  -H "Authorization: Bearer TOKEN"
```

**Response:**
```json
{
  "count": 3,
  "sources": [
    {
      "name": "ECOWAS Court",
      "url": "https://www.courtecowas.justice.org/"
    },
    {
      "name": "UN Treaties",
      "url": "https://treaties.un.org/"
    }
  ]
}
```

### 4. Add a New Source

```bash
curl -X POST http://localhost:8000/api/rag/sources/add \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cameroon Justice Ministry",
    "url": "https://www.justice.gov.cm/"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Added source: Cameroon Justice Ministry",
  "source": {
    "name": "Cameroon Justice Ministry",
    "url": "https://www.justice.gov.cm/"
  }
}
```

### 5. Remove a Source

```bash
curl -X DELETE http://localhost:8000/api/rag/sources/Cameroon%20Justice%20Ministry \
  -H "Authorization: Bearer TOKEN"
```

### 6. Update Multiple Sources

```bash
curl -X PUT http://localhost:8000/api/rag/sources/update \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ECOWAS Court": "https://www.courtecowas.justice.org/",
    "African Union": "https://au.int/",
    "UN Legal": "https://legal.un.org/"
  }'
```

---

## Manual Scraping

### 7. Scrape & Preview (Without Saving)

```bash
curl -X POST http://localhost:8000/api/rag/scrape-now \
  -H "Authorization: Bearer TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "count": 2,
  "documents": [
    {
      "id": "gov_courtecowas_1701519300",
      "source": "government_website:ECOWAS Court",
      "url": "https://www.courtecowas.justice.org/",
      "char_count": 15234,
      "preview": "The Court of Justice of the Economic Community of West African States..."
    }
  ]
}
```

### 8. Scrape & Ingest Immediately

```bash
curl -X POST http://localhost:8000/api/rag/scrape-and-ingest \
  -H "Authorization: Bearer TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "message": "Documents scraped and ingested successfully",
  "documents_scraped": 3,
  "documents_added": 3,
  "documents_skipped": 0
}
```

### 9. Scrape Custom Sources

```bash
curl -X POST http://localhost:8000/api/rag/scrape-now \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "My Law Firm": "https://example-law-firm.com/",
    "Local Courts": "https://example-courts.gov/"
  }'
```

---

## How It Works

### The Scraping Pipeline

```
1. Scheduler Trigger (every 72 hours)
   ↓
2. Web Scraper Fetches Content
   - Visits configured URLs
   - Extracts text from HTML
   - Cleans and normalizes content
   ↓
3. Content Validation
   - Checks minimum text length
   - Limits to 50KB per page
   - Adds metadata
   ↓
4. Embedding Generation
   - Converts to vectors using sentence-transformers
   - 384-dimensional embeddings
   ↓
5. RAG Storage
   - Stores in ChromaDB vector database
   - Indexed for semantic search
   ↓
6. Available for Chat
   - Users can search/chat about content
   - RAG-augmented responses
```

### Automatic Scheduling

The scheduler uses APScheduler to run tasks:
- **Non-blocking:** Runs in background without affecting API
- **Single instance:** Only one scrape at a time
- **Error handling:** Logs failures, continues normally
- **Status tracking:** Records last run time and status

---

## Configuration Examples

### Example 1: African Legal Resources

```python
from app.services.web_scraper import GovernmentWebsiteSources

sources = {
    "ECOWAS Court": "https://www.courtecowas.justice.org/",
    "African Union": "https://au.int/",
    "Pan African Parliament": "https://www.parliament.org.au/",
    "UN Treaties": "https://treaties.un.org/",
    "ICJ": "https://www.icj-cij.org/"
}

GovernmentWebsiteSources.update_sources(sources)
```

### Example 2: Country-Specific (Cameroon)

```python
sources = {
    "Cameroon Justice Ministry": "https://www.justice.gov.cm/",
    "Cameroon Court": "https://www.court-cameron.gov.cm/",
    "OHADA": "https://www.ohada.org/",  # Unified law in Africa
}

GovernmentWebsiteSources.update_sources(sources)
```

### Example 3: Legal Research

```python
sources = {
    "Google Scholar": "https://scholar.google.com/",
    "SSRN": "https://www.ssrn.com/",
    "Harvard Law": "https://law.harvard.edu/",
    "Legal Information Institute": "https://www.law.cornell.edu/",
}

GovernmentWebsiteSources.update_sources(sources)
```

---

## Monitoring & Logs

### Check Scheduler Status

```python
from app.services.rag_scheduler import get_rag_scheduler

scheduler = get_rag_scheduler()
status = scheduler.get_status()

print(f"Running: {status['is_running']}")
print(f"Last run: {status['last_run']}")
print(f"Status: {status['last_run_status']}")
print(f"Next run: {status['jobs'][0]['next_run_time']}")
```

### Application Logs

Look for messages like:

```
INFO - ✓ RAG scheduler initialized with 72h interval
INFO - 📡 Scraping government websites...
INFO - ✓ Scraped 3 documents
INFO - 🔄 Ingesting documents into RAG vector store...
INFO - ✓ Ingestion complete: 3 added, 0 skipped
```

### Troubleshooting

**Scheduler not running:**
```python
# Check enabled flag
from app.config import settings
print(f"Enabled: {settings.RAG_SCRAPE_ENABLED}")

# Check scheduler instance
from app.services.rag_scheduler import get_rag_scheduler
scheduler = get_rag_scheduler()
print(f"Running: {scheduler.is_running}")
```

**Scraper failing:**
- Check internet connectivity
- Verify URLs are accessible
- Check logs for specific errors
- Test with manual scrape endpoint

**Content not appearing:**
- Verify documents were scraped (`/api/rag/sources`)
- Check RAG search returns results (`/api/rag/search`)
- Verify ChromaDB has documents

---

## Performance Considerations

### Default Behavior
- **72-hour interval:** Balanced between freshness and server load
- **Single scraper:** Prevents concurrent scraping issues
- **Content limits:** 50KB per page prevents memory issues
- **Async operations:** Non-blocking background processing

### Optimization Tips

1. **Reduce interval for high-traffic sites:**
   ```env
   RAG_SCRAPE_INTERVAL_HOURS=24  # Daily instead of 72h
   ```

2. **Disable if not needed:**
   ```env
   RAG_SCRAPE_ENABLED=false
   ```

3. **Monitor resource usage:**
   - Check database size growth
   - Monitor memory during scrapes
   - Watch network bandwidth

---

## Best Practices

### 1. Choose Quality Sources
- Government and official legal sites
- Reputable law firms and organizations
- Peer-reviewed legal resources

### 2. Avoid Low-Quality Sources
- News sites (too much noise)
- Social media
- Unverified blogs
- NSFW content

### 3. Regular Source Audits
- Remove dead links
- Update changed URLs
- Add new relevant sources quarterly

### 4. Monitor RAG Quality
- Test search results regularly
- Verify responses are accurate
- Adjust if too much noise

### 5. Keep Documentation Updated
- Document all sources and why
- Note source reliability
- Track version changes

---

## Example Integration in Code

```python
from fastapi import FastAPI
from app.services.rag_scheduler import initialize_scheduler, shutdown_scheduler

app = FastAPI()

@app.on_event("startup")
async def startup():
    await initialize_scheduler()
    print("RAG scheduler started")

@app.on_event("shutdown")
async def shutdown():
    shutdown_scheduler()
    print("RAG scheduler stopped")
```

---

## Frequently Asked Questions

**Q: How long does scraping take?**
A: 1-5 minutes depending on website size and count. Runs in background.

**Q: Can I change the 72-hour interval?**
A: Yes, set `RAG_SCRAPE_INTERVAL_HOURS` in `.env`

**Q: What if a website is down?**
A: Scraper logs the error and continues with other sources.

**Q: Can I add my own websites?**
A: Yes, use the `/api/rag/sources/add` endpoint.

**Q: Is old content replaced?**
A: New documents are added alongside old ones. Both searchable.

**Q: Does scraping affect chat performance?**
A: No, it runs asynchronously in background.

**Q: Can I limit scraped content size?**
A: Currently 50KB per page. Edit web_scraper.py if needed.

---

**For questions or issues, check the logs or file an issue in the repository.**
