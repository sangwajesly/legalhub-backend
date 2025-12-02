# RAG Web Scraper & 72-Hour Scheduler Guide

## Overview

The LegalHub RAG system includes an **automated web scraping system** that:
- 🕐 **Runs every 72 hours** automatically
- 🌐 Scrapes government and legal websites
- 🔄 Converts content to embeddings
- 💾 Stores in the RAG vector database
- 🎯 Augments legal chat with fresh government information

---

## How It Works

### Automatic Scheduling (Every 72 Hours)

1. **Scheduler Starts** when the application boots
2. **Every 72 hours**, it automatically:
   - Scrapes configured government websites
   - Extracts legal content
   - Converts to embeddings using sentence transformers
   - Stores in ChromaDB vector database
3. **Chat System** instantly uses new information in responses

### Manual Scraping

You can trigger scraping immediately via API without waiting for the 72-hour cycle.

---

## Quick Start

### 1. Configure Government Websites

Add your government websites via API:

```bash
curl -X POST http://localhost:8000/api/rag/sources/add \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ministry of Justice",
    "url": "https://www.justice.gov.cm"
  }'
```

### 2. Check Status

```bash
curl -X GET http://localhost:8000/api/rag/scheduler/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "is_running": true,
  "last_run": "2025-12-02T10:30:00Z",
  "last_run_status": "success",
  "next_run": "2025-12-05T10:30:00Z",
  "documents_added": 245
}
```

### 3. Trigger Scraping Now (Don't Wait 72 Hours)

```bash
curl -X POST http://localhost:8000/api/rag/scheduler/run-now \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## API Endpoints

### Scheduler Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/rag/scheduler/status` | GET | Get scheduler status |
| `/api/rag/scheduler/run-now` | POST | Trigger scraping immediately |

### Website Sources

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/rag/sources` | GET | List all configured sources |
| `/api/rag/sources/add` | POST | Add a new government website |
| `/api/rag/sources/{name}` | DELETE | Remove a source |
| `/api/rag/sources/update` | PUT | Update multiple sources |

### Manual Scraping

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/rag/scrape-now` | POST | Scrape and preview (no save) |
| `/api/rag/scrape-and-ingest` | POST | Scrape and save to RAG |

---

## Detailed API Examples

### Add a Government Website

```bash
curl -X POST http://localhost:8000/api/rag/sources/add \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'name=Supreme+Court&url=https://www.supremecourt.gov'
```

### List All Sources

```bash
curl -X GET http://localhost:8000/api/rag/sources \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "count": 3,
  "sources": [
    {
      "name": "Ministry of Justice",
      "url": "https://www.justice.gov.cm"
    },
    {
      "name": "Parliament",
      "url": "https://www.parliament.gov.cm"
    },
    {
      "name": "Supreme Court",
      "url": "https://www.supremecourt.gov"
    }
  ]
}
```

### Trigger Immediate Scraping

```bash
curl -X POST http://localhost:8000/api/rag/scrape-and-ingest \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "status": "success",
  "message": "Documents scraped and ingested successfully",
  "documents_scraped": 156,
  "documents_added": 145,
  "documents_skipped": 11,
  "timestamp": "2025-12-02T14:35:00Z"
}
```

### Scrape Without Saving (Preview)

```bash
curl -X POST http://localhost:8000/api/rag/scrape-now \
  -H "Authorization: Bearer YOUR_TOKEN"
```

This returns the scraped content without saving to RAG (useful for testing).

---

## Configuration

### Environment Variables (`.env`)

```env
# RAG Scheduler Settings
RAG_ENABLE_SCHEDULER=true                    # Enable automatic scheduling
RAG_SCRAPE_INTERVAL_HOURS=72                 # Scrape interval
RAG_MAX_PAGES_PER_SITE=50                    # Max pages to crawl per site
RAG_SCRAPER_TIMEOUT=30                       # Scraper timeout (seconds)

# Default Government Websites
# Can be customized or added via API
```

### Default Government Websites

If not configured via API, the system uses these defaults:

```python
[
    {
        "name": "Ministry of Justice",
        "url": "https://www.justice.gov",
    },
    {
        "name": "Parliament/Legislature",
        "url": "https://www.parliament.gov",
    },
    {
        "name": "Court System",
        "url": "https://www.courts.gov",
    }
]
```

---

## How Scraping Works

### 1. **Fetching**
- Sends HTTP requests to government websites
- Respects robots.txt and rate limiting
- Follows internal links (same domain only)
- Max 50 pages per site (configurable)

### 2. **Parsing**
- Extracts HTML content using BeautifulSoup
- Removes scripts, styles, navigation
- Focuses on main content areas
- Cleans whitespace

### 3. **Chunking**
- Splits long documents into manageable chunks
- Preserves context between chunks
- Default: 1000 characters per chunk with 200 char overlap

### 4. **Embedding**
- Uses sentence-transformers model: `all-MiniLM-L6-v2`
- Creates 384-dimensional semantic embeddings
- Allows semantic search regardless of exact keyword match

### 5. **Storage**
- Stores in ChromaDB vector database
- Maintains metadata (URL, title, scrape date)
- Indexed for instant retrieval

---

## Example Workflow

```python
import asyncio
import httpx

async def setup_scraper():
    """Example of setting up government websites for scraping."""
    
    # Add government websites
    government_sites = [
        {
            "name": "Cameroon Ministry of Justice",
            "url": "https://www.justice.gov.cm",
        },
        {
            "name": "Cameroon Parliament",
            "url": "https://www.assemblee-nationale.cm",
        },
        {
            "name": "Cameroon Supreme Court",
            "url": "https://www.cour-de-cassation.cm",
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for site in government_sites:
            response = await client.post(
                "http://localhost:8000/api/rag/sources/add",
                headers={"Authorization": "Bearer YOUR_TOKEN"},
                params={
                    "name": site["name"],
                    "url": site["url"]
                }
            )
            print(f"Added: {site['name']}")
    
    # Trigger scraping
    response = await client.post(
        "http://localhost:8000/api/rag/scheduler/run-now",
        headers={"Authorization": "Bearer YOUR_TOKEN"}
    )
    print(f"Scraping result: {response.json()}")

asyncio.run(setup_scraper())
```

---

## Monitoring & Debugging

### Check Scheduler Status

```bash
curl -X GET http://localhost:8000/api/rag/scheduler/status \
  -H "Authorization: Bearer YOUR_TOKEN" | jq
```

### View Last Run Details

The scheduler logs to the application console:

```
🚀 Starting RAG scheduler (runs every 72 hours)
📡 Scraping government websites...
✓ Scraped 156 documents
🔄 Ingesting documents into RAG vector store...
✓ Ingestion complete: 145 added, 11 skipped
```

### Check Logs

```bash
# View real-time logs
tail -f logs/app.log | grep "RAG"

# Search for scraping logs
grep -i "scrape\|ingest" logs/app.log
```

---

## Best Practices

### 1. **Website Selection**
- ✅ Government official websites
- ✅ Legal repositories
- ✅ Court decision databases
- ❌ Avoid: Blogs, social media, non-legal content

### 2. **Rate Limiting**
- Scraper respects website policies
- Uses delays between requests
- Identifies as a bot in User-Agent
- Never scrapes too aggressively

### 3. **Content Quality**
- Focuses on main content areas
- Skips navigation, ads, footers
- Minimum 100 chars per page
- Maximum 5000 chars per page

### 4. **Error Handling**
- Automatically retries failed requests
- Logs all errors for debugging
- Continues with next site on failure
- Graceful degradation

### 5. **Performance**
- Runs asynchronously (non-blocking)
- Parallel requests to multiple sites
- Efficient embedding generation
- Batch ingestion to RAG

---

## Troubleshooting

### Scraper Not Running

**Problem:** Scheduled scraping doesn't happen
```bash
# Solution: Check scheduler status
curl -X GET http://localhost:8000/api/rag/scheduler/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Check `is_running` is `true` and `next_run` is in the future.

### No Documents Scraped

**Problem:** Scraping returns 0 documents
```
# Check if websites are accessible
curl -I https://www.justice.gov.cm

# Try manual scraping to debug
curl -X POST http://localhost:8000/api/rag/scrape-now \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Embeddings Not Updating Chat

**Problem:** Chat doesn't use new scraped content
```bash
# Verify documents were added to RAG
curl -X GET http://localhost:8000/api/rag/search \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "government", "top_k": 10}'
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                  │
├─────────────────────────────────────────────────────────┤
│  API Routes (rag_scraper.py)                            │
│  ├─ /scheduler/status                                   │
│  ├─ /scheduler/run-now                                  │
│  ├─ /sources/* (CRUD)                                   │
│  └─ /scrape-* (manual triggers)                         │
├─────────────────────────────────────────────────────────┤
│  Services                                               │
│  ├─ RAGScrapeScheduler                                  │
│  │  └─ Runs every 72 hours via APScheduler              │
│  ├─ WebScraper                                          │
│  │  └─ Fetches and extracts content                     │
│  └─ RAGService                                          │
│     └─ Stores embeddings in ChromaDB                    │
├─────────────────────────────────────────────────────────┤
│  Storage                                                │
│  ├─ ChromaDB (vector store with embeddings)             │
│  └─ Government website content (cached)                 │
└─────────────────────────────────────────────────────────┘
```

---

## Security Considerations

1. **Authentication:** All endpoints require valid auth token
2. **Rate Limiting:** Respects website robots.txt
3. **User-Agent:** Identifies as bot to websites
4. **SSL Verification:** Configurable for self-signed certs
5. **Timeout Protection:** 30-second default timeout
6. **Error Logging:** All errors logged, never exposes credentials

---

## Performance Metrics

Typical performance for a 72-hour scrape cycle:

- **Time to scrape 3 sites (150 pages):** ~3-5 minutes
- **Time to generate embeddings:** ~2-3 minutes  
- **Time to store in RAG:** ~1 minute
- **Total cycle time:** ~6-9 minutes (minimal overhead)
- **Chat query response time:** <1 second (vectors pre-indexed)

---

## Next Steps

1. **Add government websites** via `/api/rag/sources/add`
2. **Trigger manual scraping** via `/api/rag/scheduler/run-now`
3. **Monitor status** via `/api/rag/scheduler/status`
4. **Verify in chat** by asking questions about government info

The system will then **automatically run every 72 hours** to keep your knowledge base fresh! 🚀
