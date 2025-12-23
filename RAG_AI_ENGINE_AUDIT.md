# LegalHub RAG & AI Engine Audit Report

## Audit Summary

The RAG (Retrieval-Augmented Generation) pipeline for LegalHub has been thoroughly reviewed and tested. The core infrastructure for document ingestion, vector storage (FAISS), and similarity retrieval is **fully functional**. Several critical improvements were made during this audit to ensure reliability and search accuracy.

## Current Component Status

| Component              | Status        | Details                                                                   |
| ---------------------- | ------------- | ------------------------------------------------------------------------- |
| **FAISS Vector Store** | ✅ Functional | Persistent storage in `./chroma_db/`. Uses `all-MiniLM-L6-v2` embeddings. |
| **PDF Processor**      | ✅ Functional | Robust text extraction using `pypdf`.                                     |
| **Document Ingestion** | ✅ Functional | Supports batch PDF loading and individual document addition via API.      |
| **Similarity Search**  | ✅ Improved   | Switched from relative to absolute cosine similarity scoring.             |
| **RAG Orchestration**  | ✅ Functional | `RAGService` correctly handles prompt augmentation and LLM calls.         |
| **Gemini Integration** | ⚠️ Limited    | Functional but currently restricted by free-tier quota (20 req/day).      |
| **Scraper Scheduler**  | ✅ Functional | Periodic updates (every 72h) of legal documents from government sites.    |

## Improvements & Fixes

### 1. FAISS Store Lazy Initialization

- **Problem:** The `count()` method returned `0` if the store hadn't been triggered by an `add` or `search` operation yet, even if an index existed on disk.
- **Fix:** Added `self._ensure_initialized()` to the `count()` method to ensure documents are loaded from disk before reporting counts.

### 2. Similarity Scoring Logic

- **Problem:** The previous logic used "relative normalization" within the top K results. This meant the least similar result in any search always got a score of `0.0`, regardless of how relevant it actually was. This caused many relevant documents to be filtered out by the 0.3 threshold.
- **Fix:** Implemented absolute cosine similarity calculation: `score = 1.0 - (L2_distance / 2.0)`. This provides a stable 0-1 metric that accurately reflects document relevance.

### 3. Verification Tools

- Created `inspect_faiss.py` to easily monitor the state of the vector store.
- Re-tested searches with actual legal text from the Cameroon Constitution.

## Recommendations

### 1. LLM Quota Management

The current `gemini-2.5-flash` free tier is extremely limited (20 requests/day).

- **Recommendation:** Upgrade to a paid plan or implement a model-switching fallback (e.g., using `gemini-1.5-flash` or OpenAI/Anthropic if available).
- **Interim:** Enable `DEBUG_MOCK_GEMINI=true` in `.env` for development and UI testing to save quota for production verification.

### 2. Streaming Enhancement

Currently, `stream_send_message` in `gemini_service.py` is a wrapper that yields the full response after it's finished.

- **Recommendation:** Implement true SSE (Server-Sent Events) streaming by consuming the Gemini streaming API chunks as they arrive.

### 3. Persistence Refactoring

The storage path is still named `chroma_db` although it uses FAISS.

- **Recommendation:** Rename `CHROMADB_PATH` to `VECTOR_STORE_PATH` in `config.py` and update existing directories to avoid developer confusion.

---

_Audit conducted on 2025-12-20_
