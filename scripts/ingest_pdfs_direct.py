"""
Direct PDF Ingestion Script — Gemini Embedding Edition
=======================================================
Uses Google Gemini text-embedding-004 (768-dim) for all embeddings.
NO torch / sentence-transformers required.

Usage:
    uv run python scripts/ingest_pdfs_direct.py --reset
    uv run python scripts/ingest_pdfs_direct.py          # adds new PDFs only

Rate limit: Gemini free tier allows 1,500 embedding requests/min.
            Script pauses 0.1s between API calls to be safe.
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
                retry: int = 3) -> list:
    """Embed texts via Gemini REST API (no SDK — avoids Windows crashes)."""
    embeddings = []
    for i, text in enumerate(texts):
        for attempt in range(retry):
            try:
                resp = requests.post(
                    EMBED_URL,
                    params={"key": GOOGLE_API_KEY},
                    json={
                        "model": f"models/{EMBED_MODEL}",
                        "content": {"parts": [{"text": text}]},
                        "taskType": task_type,
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                embeddings.append(resp.json()["embedding"]["values"])
                time.sleep(0.05)   # ~20 req/s — safe under rate limits
                break
            except Exception as e:
                wait = 2 ** attempt
                print(f"         [embed retry {attempt+1}/{retry} — {e} — wait {wait}s]")
                time.sleep(wait)
        else:
            raise RuntimeError(f"Embedding failed after {retry} retries for text #{i}")
    return embeddings

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

    def add(self, docs: list, embeddings: list) -> int:
        self.index.add(np.array(embeddings, dtype="float32"))
        self.documents.extend(docs)
        self._save()
        return len(docs)

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
    parser.add_argument("--batch-size", type=int, default=10,
                        help="Chunks to embed per batch (default 10)")
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
    success = skipped = failed = total_chunks = 0

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
            for k in range(0, len(documents), args.batch_size):
                batch     = documents[k:k + args.batch_size]
                texts     = [d["content"] for d in batch]
                embeddings = embed_texts(texts, task_type="retrieval_document")
                added     += store.add(batch, embeddings)
                sys.stdout.write(f"\r         -> Embedded {min(k+args.batch_size, len(documents))}/{len(documents)} chunks...")
                sys.stdout.flush()

            print(f"\r         -> Added {added} chunks  [Total in store: {store.count()}]")
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
    print(f"  Skipped   : {skipped}  (image/scanned PDFs)")
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
