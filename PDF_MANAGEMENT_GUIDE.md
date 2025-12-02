# PDF Management Guide for LegalHub RAG

## Overview

LegalHub has a complete PDF handling system for the RAG (Retrieval-Augmented Generation) pipeline. You can add PDFs in multiple ways:

---

## Quick Start

**Recommended**: Just put PDFs in `/data/pdfs/` and run:

```bash
python scripts/batch_load_pdfs.py
```

That's it! Your PDFs are now indexed and searchable.

---

## Method 1: Batch Load from `/data/pdfs` Folder (RECOMMENDED)

### Setup
Simply place all your PDF documents in the `/data/pdfs` folder:

```
legalhub-backend/
├── data/
│   └── pdfs/
│       ├── contract_law.pdf
│       ├── criminal_code.pdf
│       └── ...more pdfs...
│   ├── chroma_db/           # Vector database storage
│   └── ...
├── scripts/
│   └── batch_load_pdfs.py       # Batch loader script
└── app/
    ├── services/
    │   ├── rag_service.py          # Main RAG orchestration
    │   ├── embedding_service.py    # Embeddings generation
    │   └── pdf_processor.py        # PDF text extraction
    ├── api/routes/
    │   └── rag.py                  # RAG API endpoints
    └── utils/
        └── vector_store.py         # ChromaDB management
```

---

## Storage & Vector Database

### ChromaDB Collections

All ingested documents are stored in ChromaDB with semantic embeddings:

- **Collection:** `legalhub_documents`
- **Embedding Model:** `all-MiniLM-L6-v2` (384-dimensional)
- **Storage:** Persistent in `/data/chroma_db`

### Document Metadata

Each document in the vector store includes:
- `id`: Unique identifier
- `content`: Full text content
- `source`: Where it came from (pdf:filename, statute, article, etc.)
- `metadata`: Additional info (pages, size, dates, etc.)

---

## Best Practices

### 1. **Organization**
Keep PDFs organized by category:
```
data/pdfs/
├── criminal_law/
│   ├── criminal_code.pdf
│   └── criminal_procedure.pdf
├── civil_law/
│   ├── civil_code.pdf
│   └── contract_law.pdf
└── corporate/
    └── corporate_law.pdf
```

### 2. **Naming Conventions**
- Use descriptive names: `cameroon_penal_code.pdf` ✅
- Avoid: `document1.pdf` ❌
- Use underscores: `contract_law_2024.pdf` ✅

### 3. **File Size Limits**
- Individual PDFs: < 50MB recommended
- System tested with 200K+ character PDFs
- If too large, split into chapters

### 4. **Quality Checks**
- Ensure PDFs have extractable text (not scanned images)
- Run test extraction first:

```python
from app.services.pdf_processor import PDFProcessor

processor = PDFProcessor()
with open("your_pdf.pdf", "rb") as f:
    text, metadata = processor.extract_text_from_pdf(f.read())
    
print(f"Extracted {len(text)} characters")
print(f"Metadata: {metadata}")
```

---

## Troubleshooting

### "No PDF files found in folder"
```bash
# Check folder exists
ls data/pdfs/

# Move PDFs to correct location
mv *.pdf data/pdfs/
```

### "Insufficient text extracted"
- PDF is scanned (image-based) - needs OCR
- PDF is corrupted - try different reader
- Text is encrypted - decrypt first

### Search returns no results
- Use `top_k=10` to expand results
- Lower `score_threshold` (default 0.3)
- Verify documents were added:

```python
from app.utils.vector_store import get_chroma_client
client = get_chroma_client()
collection = client.get_collection("legalhub_documents")
print(f"Total documents: {collection.count()}")
```

---

## API Endpoints Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/rag/documents/upload` | POST | Upload single file |
| `/api/rag/documents/add` | POST | Add multiple documents |
| `/api/rag/search` | POST | Search vector store |
| `/api/rag/chat/message` | POST | Chat with RAG augmentation |

---

## Example Workflow

```bash
# 1. Place PDFs in folder
cp /path/to/pdfs/*.pdf data/pdfs/

# 2. Load into RAG
python scripts/batch_load_pdfs.py --cleanup

# 3. Test via API
curl -X POST http://localhost:8000/api/rag/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"query": "What is contract law?", "top_k": 5}'

# 4. Chat with RAG augmentation
curl -X POST http://localhost:8000/api/rag/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "sessionId": "session_123",
    "message": "Explain contract formation",
    "use_rag": true,
    "top_k": 3
  }'
```

---

## Configuration

Edit `.env` for RAG settings:

```env
# Vector Store
CHROMA_STORAGE_PATH=/data/chroma_db
CHROMA_USE_MEMORY=false  # Use persistent storage

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# RAG Search Parameters
RAG_DEFAULT_TOP_K=5
RAG_DEFAULT_THRESHOLD=0.3

# LLM Integration
GEMINI_MODEL=gemini-2.5-flash
GOOGLE_API_KEY=your_key_here
```

---

## Performance Tips

1. **Batch Loading:** Load all PDFs at once for efficiency
2. **Indexing:** ChromaDB auto-indexes on add
3. **Caching:** Embeddings cached after first computation
4. **Search:** Query results cached for 5 minutes

---

**Questions?** Check the RAG service implementation in `app/services/rag_service.py` or run the test suite:

```bash
python test_rag_system.py
```
    "top_k": 3
  }'
```

**Response:**
```json
{
  "reply": "Based on the provided legal context, the essential elements of a valid contract are: 1. Offer 2. Acceptance 3. Consideration...",
  "sessionId": "session_123"
}
```

---

## Configuration

### Chunk Size Settings

- **Small (500-800)**: Better for precise answers, more chunks
- **Medium (1000)**: Balanced, recommended default
- **Large (1500+)**: Better for context, fewer chunks

### Score Threshold

- **0.1-0.3**: Broad search, may include loosely related docs
- **0.3-0.5**: Balanced, good general purpose
- **0.5-1.0**: Strict, only highly relevant documents

### Collection Names

- `legalhub_documents` (default): Main production collection
- `test_documents`: For testing/development
- Custom names: Organize by category or jurisdiction

---

## Troubleshooting

### Issue: "No PDFs found"
```bash
# Check folder exists and has PDFs
ls data/pdfs/
# Ensure files are .pdf extension (case-sensitive on Linux)
find data/pdfs -name "*.pdf"
```

### Issue: Out of memory with large PDFs
```bash
# Reduce chunk size
python scripts/load_pdfs.py --chunk-size 500 --chunk-overlap 100
```

### Issue: Poor search results
```bash
# Lower the score threshold in search
# Use more specific queries
# Check document content is properly formatted
```

### Issue: Slow ingestion
```bash
# Normal for large documents (1000+ pages)
# Consider splitting into smaller PDFs
# Batch processing runs sequentially
```

---

## Monitoring & Maintenance

### Check loaded documents count
```python
from app.utils.vector_store import get_chroma_client

client = get_chroma_client()
collection = client.get_collection("legalhub_documents")
print(f"Total chunks: {collection.count()}")
```

### Clear a collection (careful!)
```python
from app.utils.vector_store import get_chroma_client

client = get_chroma_client()
client.delete_collection("legalhub_documents")
```

### Monitor ChromaDB storage
```bash
# Check disk usage
du -sh legalhub_chroma/
ls -lh legalhub_chroma/
```

---

## Performance Tips

1. **Batch Load During Off-Hours**: Large batch loads can take time
2. **Use Appropriate Chunk Sizes**: Balance between context and precision
3. **Regular Cleanup**: Archive old/irrelevant documents
4. **Collection Separation**: Use different collections for different jurisdictions
5. **Monitor Memory**: Keep track of ChromaDB collection size

---

## File Format Support

| Format | Support | Method |
|--------|---------|--------|
| PDF | ✓ Full | Batch loader or API upload |
| TXT | ✓ Full | API upload or direct ingestion |
| Markdown | ✓ Full | API upload or direct ingestion |
| DOCX | ~ Partial | Convert to TXT/PDF first |
| Images/Scanned | ✗ None | Requires OCR preprocessing |

---

## Next Steps

1. Place legal documents in `/data/pdfs/`
2. Run `python scripts/load_pdfs.py`
3. Test with `/api/rag/search` endpoint
4. Use RAG-enhanced chat at `/api/rag/chat/message`
5. Monitor performance and adjust chunk sizes as needed

For API documentation, see `/api/rag` endpoints.
