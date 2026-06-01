"""
Direct PDF Ingestion Script — Gemini Embedding Edition
=======================================================
Uses Google Gemini text-embedding-004 (768-dim) for all embeddings.
NO torch / sentence-transformers required.

Usage:
    uv run python scripts/ingest_pdfs_direct.py --reset
    uv run python scripts/ingest_pdfs_direct.py          # adds new PDFs only

Rate limit: Gemini free tier allows 1,500 embedding requests/min.
            Script pauses 0.05s between API calls to be safe.
"""

import sys
import os
import re
import pickle
import time
import logging
import argparse
from pathlib import Path

logging.basicConfig(level=logging.WARNING)

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Load .env without importing app.* (avoids the google/jinja2 crash chain)
# ---------------------------------------------------------------------------
def _read_env() -> dict:
    env = {}
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env

_ENV = _read_env()
GOOGLE_API_KEY = _ENV.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))
CHROMADB_PATH  = _ENV.get("CHROMADB_PATH", str(PROJECT_ROOT / "chroma_db"))

# ---------------------------------------------------------------------------
# Gemini embedding (gemini-embedding-001, 3072-dim) via direct REST
# ---------------------------------------------------------------------------
import requests
import faiss
import numpy as np

EMBED_MODEL = "gemini-embedding-001"
DIMENSION   = 3072
EMBED_URL   = f"https://generativelanguage.googleapis.com/v1/models/{EMBED_MODEL}:embedContent"

def embed_texts(texts: list, task_type: str = "RETRIEVAL_DOCUMENT",
                retry: int = 3, base_wait: float = 0.05) -> list:
    """Embed texts via Gemini REST API (no SDK — avoids Windows crashes).
    Upgraded to use the batchEmbedContents endpoint for high performance and zero 429 errors.
    """
    if not texts:
        return []

    batch_url = f"https://generativelanguage.googleapis.com/v1/models/{EMBED_MODEL}:batchEmbedContents"
    
    # Standardize task type to uppercase as required by Gemini API
    api_task_type = task_type.upper() if task_type else "RETRIEVAL_DOCUMENT"

    # Construct the batch request payload
    requests_payload = []
    for text in texts:
        requests_payload.append({
            "model": f"models/{EMBED_MODEL}",
            "content": {"parts": [{"text": text}]},
            "taskType": api_task_type,
        })

    payload = {"requests": requests_payload}

    for attempt in range(retry):
        try:
            resp = requests.post(
                batch_url,
                params={"key": GOOGLE_API_KEY},
                json=payload,
                timeout=45,
            )
            resp.raise_for_status()
            data = resp.json()
            embeddings = [emb["values"] for emb in data.get("embeddings", [])]
            time.sleep(base_wait)
            return embeddings
        except Exception as e:
            wait = 2 ** attempt
            print(f"         [batch embed retry {attempt+1}/{retry} — {e} — wait {wait}s]")
            time.sleep(wait)

    raise RuntimeError(f"Batch embedding failed after {retry} retries.")

# ---------------------------------------------------------------------------
# PDF text extraction (pure Python — no app.* imports)
# ---------------------------------------------------------------------------
import io as _io

def extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(_io.BytesIO(pdf_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        print(f"         [pypdf error: {e}]")
        return ""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def classify_by_filename(filename: str) -> dict:
    name = filename.lower()
    if "constitution" in name:
        return {"document_type": "Constitution", "legal_domain": "Constitutional Law"}
    elif "penal" in name or "criminal" in name:
        return {"document_type": "Statute", "legal_domain": "Criminal Law"}
    elif "electoral" in name:
        return {"document_type": "Statute", "legal_domain": "Administrative Law"}
    elif "mining" in name:
        return {"document_type": "Statute", "legal_domain": "Corporate Law"}
    elif "finance" in name or "budget" in name:
        return {"document_type": "Statute", "legal_domain": "Administrative Law"}
    elif "customary" in name or "women" in name or "family" in name:
        return {"document_type": "Other", "legal_domain": "Family Law"}
    else:
        return {"document_type": "Statute", "legal_domain": "Other"}


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    chunks, start = [], 0
    while start < len(text):
        chunk = text[start:start + chunk_size]
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# ---------------------------------------------------------------------------
# Minimal FAISS store (no app.* imports)
# ---------------------------------------------------------------------------
class DirectFAISSStore:
    def __init__(self, path: str, name: str = "legalhub_documents"):
        self.path = path
        self.name = name
        self.index = faiss.IndexFlatL2(DIMENSION)
        self.documents = []
        self._load()

    def _paths(self):
        os.makedirs(self.path, exist_ok=True)
        return (
            os.path.join(self.path, f"{self.name}.faiss"),
            os.path.join(self.path, f"{self.name}_docs.pkl"),
        )

    def _load(self):
        idx_path, docs_path = self._paths()
        if os.path.exists(idx_path) and os.path.exists(docs_path):
            try:
                self.index = faiss.read_index(idx_path)
                with open(docs_path, "rb") as f:
                    self.documents = pickle.load(f)
                print(f"[OK] Loaded existing index: {len(self.documents)} chunks")
            except Exception as e:
                print(f"[WARN] Could not load index: {e}. Starting fresh.")
        else:
            print("[OK] No existing index — starting fresh.")

    def reset(self):
        self.index = faiss.IndexFlatL2(DIMENSION)
        self.documents = []
        self._save()
        print("[OK] Index reset (empty).")

    def _document_ids(self):
        return {doc["id"] for doc in self.documents}

    def document_ids_for_prefix(self, prefix: str) -> set:
        prefix_token = f"{prefix}_chunk_"
        return {doc_id for doc_id in self._document_ids() if doc_id.startswith(prefix_token)}

    def has_document_prefix(self, prefix: str) -> bool:
        return bool(self.document_ids_for_prefix(prefix))

    def add(self, docs: list, embeddings: list) -> int:
        existing_ids = self._document_ids()
        deduped_docs = []
        deduped_embeddings = []

        for doc, emb in zip(docs, embeddings):
            if doc["id"] in existing_ids:
                continue
            deduped_docs.append(doc)
            deduped_embeddings.append(emb)

        if not deduped_docs:
            print("[OK] All chunks already exist in FAISS. Nothing to add.")
            return 0

        self.index.add(np.array(deduped_embeddings, dtype="float32"))
        self.documents.extend(deduped_docs)
        self._save()
        return len(deduped_docs)

    def count(self) -> int:
        return len(self.documents)

    def _save(self):
        idx_path, docs_path = self._paths()
        faiss.write_index(self.index, idx_path)
        with open(docs_path, "wb") as f:
            pickle.dump(self.documents, f)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Ingest PDFs into FAISS using Gemini embeddings")
    parser.add_argument("--pdf-folder", default=str(PROJECT_ROOT / "data" / "pdfs"))
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--overlap",    type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=100,
                        help="Chunks to embed per batch (default 100)")
    parser.add_argument("--embed-delay", type=float, default=0.05,
                        help="Seconds to wait after each embedding request (default 0.05)")
    parser.add_argument("--reset",      action="store_true",
                        help="Clear the store before ingesting")
    args = parser.parse_args()

    # Verify API key
    if not GOOGLE_API_KEY:
        print("ERROR: GOOGLE_API_KEY not found in .env or environment.")
        sys.exit(1)

    pdf_folder = Path(args.pdf_folder)
    if not pdf_folder.exists():
        print(f"ERROR: PDF folder not found: {pdf_folder}")
        sys.exit(1)

    pdf_files = sorted(pdf_folder.glob("*.pdf"))
    if not pdf_files:
        print(f"ERROR: No PDFs in {pdf_folder}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("LegalHub Direct PDF Ingestion  [Gemini text-embedding-004]")
    print(f"{'='*60}")
    print(f"PDF Folder : {pdf_folder}")
    print(f"PDFs Found : {len(pdf_files)}")
    print(f"Chunk Size : {args.chunk_size} chars  |  Overlap: {args.overlap} chars")
    print(f"Embed Dim  : {DIMENSION}  (Gemini text-embedding-004)")
    print(f"FAISS Path : {CHROMADB_PATH}")
    print(f"{'='*60}\n")

    store = DirectFAISSStore(CHROMADB_PATH)

    if args.reset:
        print("Resetting vector store...")
        store.reset()
        print()

    total = len(pdf_files)
    success = skipped = failed = total_chunks = duplicate_chunks_skipped = duplicate_documents_skipped = 0

    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{total}] {pdf_path.name}")
        try:
            text = extract_pdf_text(pdf_path.read_bytes())

            if not text or len(text.strip()) < 100:
                print(f"         -> SKIPPED (no extractable text — likely scanned PDF)")
                skipped += 1
                continue

            clf    = classify_by_filename(pdf_path.name)
            chunks = chunk_text(text, args.chunk_size, args.overlap)
            print(f"         -> {len(text):,} chars | {len(chunks)} chunks | {clf['legal_domain']}")

            doc_id    = re.sub(r"[^a-zA-Z0-9_]", "_", pdf_path.stem)[:60]
            document_chunk_ids = {f"{doc_id}_chunk_{j}" for j in range(len(chunks))}
            existing_chunk_ids = store.document_ids_for_prefix(doc_id)

            if document_chunk_ids <= existing_chunk_ids:
                print(f"         -> SKIPPED (document already fully embedded in FAISS)")
                duplicate_documents_skipped += 1
                duplicate_chunks_skipped += len(document_chunk_ids)
                skipped += 1
                continue

            if existing_chunk_ids:
                print(f"         -> Partial document already embedded, appending missing chunks")

            documents = [
                {
                    "id":            f"{doc_id}_chunk_{j}",
                    "content":       chunk,
                    "source":        f"pdf:{pdf_path.name}",
                    "filename":      pdf_path.name,
                    "document_type": clf["document_type"],
                    "legal_domain":  clf["legal_domain"],
                    "jurisdiction":  "Cameroon",
                    "chunk_index":   j,
                }
                for j, chunk in enumerate(chunks)
            ]

            # Embed in batches
            added = 0
            batch_skipped = 0
            for k in range(0, len(documents), args.batch_size):
                batch     = documents[k:k + args.batch_size]
                texts     = [d["content"] for d in batch]
                try:
                    embeddings = embed_texts(texts, task_type="retrieval_document", base_wait=args.embed_delay)
                    batch_added = store.add(batch, embeddings)
                    added += batch_added
                    batch_skipped += len(batch) - batch_added
                except Exception as e:
                    print(f"\n         -> WARNING: embedding batch failed: {e}  -- skipping this batch and continuing")
                    # continue with remaining batches
                    continue
                sys.stdout.write(f"\r         -> Embedded {min(k+args.batch_size, len(documents))}/{len(documents)} chunks...")
                sys.stdout.flush()

            duplicate_chunks_skipped += batch_skipped
            print(f"\r         -> Added {added} chunks  [Skipped {batch_skipped} duplicate chunks] [Total in store: {store.count()}]")
            total_chunks += added
            success += 1

        except Exception as e:
            print(f"         -> FAILED: {e}")
            import traceback; traceback.print_exc()
            failed += 1

    print(f"\n{'='*60}")
    print("Ingestion Complete!")
    print(f"{'='*60}")
    print(f"  Processed : {total}")
    print(f"  Succeeded : {success}")
    print(f"  Skipped   : {skipped}  (image/scanned or fully duplicated PDFs)")
    print(f"  Duplicate chunks skipped: {duplicate_chunks_skipped}")
    print(f"  Duplicate documents skipped: {duplicate_documents_skipped}")
    print(f"  Failed    : {failed}")
    print(f"  Chunks    : {total_chunks} added | {store.count()} total in index")
    print(f"{'='*60}")

    if success == 0:
        sys.exit(1)

    print(f"\n{'='*60}")
    print("Next: commit the new index to Git so Vercel picks it up")
    print(f"{'='*60}")
    print(f"  git add chroma_db/")
    print(f'  git commit -m "chore: rebuild FAISS index with Gemini embeddings ({total_chunks} chunks)"')
    print(f"  git push")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
