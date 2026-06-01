"""
Direct Text-based Ingestion Script — Page Number Edition
======================================================
Reads pre-extracted .txt files from `data/extracted_texts/` (which contain [Page X] markers),
splits them into chunks on a page-by-page basis (preserving exact page metadata),
and embeds them into the FAISS index using the high-performance Gemini batchEmbedContents endpoint.

Usage:
    .venv/Scripts/python scripts/ingest_texts_direct.py --reset
    .venv/Scripts/python scripts/ingest_texts_direct.py          # appends new files only
"""

import sys
import os
import re
import pickle
import time
import argparse
from pathlib import Path
import requests
import faiss
import numpy as np

# Resolve project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Config loader (avoids deep imports to stay lightweight)
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

EMBED_MODEL = "gemini-embedding-2"
DIMENSION   = 3072

# ---------------------------------------------------------------------------
# Gemini Batch Embedding API helper
# ---------------------------------------------------------------------------
def embed_texts(texts: list, task_type: str = "RETRIEVAL_DOCUMENT",
                 retry: int = 10, base_wait: float = 0.05) -> list:
    """Embed texts via Gemini REST API batch endpoint."""
    if not texts:
        return []

    batch_url = f"https://generativelanguage.googleapis.com/v1/models/{EMBED_MODEL}:batchEmbedContents"
    api_task_type = task_type.upper() if task_type else "RETRIEVAL_DOCUMENT"

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
            is_429 = "429" in str(e) or (hasattr(e, "response") and e.response is not None and getattr(e.response, "status_code", None) == 429)
            if is_429:
                wait = 5 * (2 ** attempt)
                print(f"\n         [batch embed rate-limited (429) retry {attempt+1}/{retry} — waiting {wait}s]")
            else:
                wait = 2 ** attempt
                print(f"\n         [batch embed error retry {attempt+1}/{retry} — {e} — waiting {wait}s]")
            
            sys.stdout.flush()
            time.sleep(wait)

    raise RuntimeError(f"Batch embedding failed after {retry} retries.")


# ---------------------------------------------------------------------------
# Parsing & Chunking helpers
# ---------------------------------------------------------------------------
def extract_pages(text: str) -> list:
    """Extract page number and clean text blocks from the [Page X] tags."""
    pattern = r'\[Page (\d+)\]'
    matches = list(re.finditer(pattern, text))
    
    if not matches:
        return [(1, text)]
        
    pages = []
    for i in range(len(matches)):
        start_idx = matches[i].end()
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(text)
        page_num = int(matches[i].group(1))
        page_text = text[start_idx:end_idx].strip()
        if page_text:
            pages.append((page_num, page_text))
            
    return pages


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
    """Standard character-level text chunker."""
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start:start + chunk_size]
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


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


# ---------------------------------------------------------------------------
# Direct FAISS Store Manager
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
                print(f"[OK] Loaded existing FAISS index: {len(self.documents)} chunks")
            except Exception as e:
                print(f"[WARN] Could not load FAISS index: {e}. Starting fresh.")
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
# Main Execution Loop
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Ingest extracted text files into FAISS preserving page numbers")
    parser.add_argument("--text-folder", default=str(PROJECT_ROOT / "data" / "extracted_texts"))
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--overlap",    type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=100,
                        help="Chunks to embed per API request (max 100)")
    parser.add_argument("--embed-delay", type=float, default=0.05,
                        help="Pause between requests (seconds)")
    parser.add_argument("--reset",      action="store_true",
                        help="Clear index before embedding")
    args = parser.parse_args()

    if not GOOGLE_API_KEY:
        print("ERROR: GOOGLE_API_KEY not found in .env or environment.")
        sys.exit(1)

    text_folder = Path(args.text_folder)
    if not text_folder.exists():
        print(f"ERROR: Text folder not found: {text_folder}")
        sys.exit(1)

    txt_files = sorted(text_folder.glob("*.txt"))
    if not txt_files:
        print(f"ERROR: No extracted text files found in {text_folder}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("LegalHub Direct Text Ingestion — Page-Preserving Edition")
    print(f"{'='*60}")
    print(f"Text Folder: {text_folder}")
    print(f"Files Found: {len(txt_files)}")
    print(f"Chunk Size : {args.chunk_size} chars  |  Overlap: {args.overlap} chars")
    print(f"Embed Dim  : {DIMENSION}  (Gemini text-embedding-004)")
    print(f"FAISS Path : {CHROMADB_PATH}")
    print(f"{'='*60}\n")

    store = DirectFAISSStore(CHROMADB_PATH)

    if args.reset:
        print("Resetting vector store index...")
        store.reset()
        print()

    total = len(txt_files)
    success = skipped = failed = total_chunks = duplicate_chunks_skipped = 0

    for i, txt_path in enumerate(txt_files, 1):
        print(f"[{i}/{total}] {txt_path.name}")
        try:
            text = txt_path.read_text(encoding="utf-8", errors="ignore")

            if not text or len(text.strip()) < 50:
                print(f"         -> SKIPPED (empty or too short)")
                skipped += 1
                continue

            # Classify legal domains
            clf = classify_by_filename(txt_path.name)
            
            # Extract page blocks
            pages = extract_pages(text)
            print(f"         -> {len(text):,} chars | {len(pages)} pages | {clf['legal_domain']}")

            # Clean document ID for FAISS tracking
            doc_id = re.sub(r"[^a-zA-Z0-9_]", "_", txt_path.stem)[:60]
            
            # Check if this document has already been partially or fully ingested
            existing_chunk_ids = store.document_ids_for_prefix(doc_id)
            if existing_chunk_ids and not args.reset:
                print(f"         -> Found {len(existing_chunk_ids)} existing chunks in FAISS (checking for missing chunks)...")

            # Build list of document chunks (filtering out already existing chunk IDs)
            documents = []
            skipped_chunks = 0
            for page_num, page_text in pages:
                chunks = chunk_text(page_text, args.chunk_size, args.overlap)
                for chunk_idx, chunk in enumerate(chunks):
                    chunk_id = f"{doc_id}_chunk_{page_num}_{chunk_idx}"
                    if chunk_id in existing_chunk_ids and not args.reset:
                        skipped_chunks += 1
                        continue
                    documents.append({
                        "id":            chunk_id,
                        "content":       chunk,
                        "source":        f"pdf:{txt_path.stem}.pdf", # Keep .pdf source for consistency
                        "filename":      f"{txt_path.stem}.pdf",
                        "document_type": clf["document_type"],
                        "legal_domain":  clf["legal_domain"],
                        "jurisdiction":  "Cameroon",
                        "page":          page_num,
                        "chunk_index":   chunk_idx,
                    })

            if not documents:
                print(f"         -> SKIPPED (all {skipped_chunks} chunks already exist in FAISS)")
                skipped += 1
                continue
            
            if skipped_chunks > 0:
                print(f"         -> Skipping {skipped_chunks} already ingested chunks. Ingesting remaining {len(documents)} chunks...")

            # Embed in batches using batchEmbedContents
            added = 0
            batch_skipped = 0
            for k in range(0, len(documents), args.batch_size):
                batch = documents[k:k + args.batch_size]
                texts = [d["content"] for d in batch]
                try:
                    embeddings = embed_texts(texts, task_type="retrieval_document", base_wait=args.embed_delay)
                    batch_added = store.add(batch, embeddings)
                    added += batch_added
                    batch_skipped += len(batch) - batch_added
                except Exception as e:
                    print(f"\n         -> CRITICAL ERROR: embedding batch failed: {e}")
                    raise e
                sys.stdout.write(f"\r         -> Embedded {min(k+args.batch_size, len(documents))}/{len(documents)} chunks...")
                sys.stdout.flush()

            duplicate_chunks_skipped += batch_skipped
            print(f"\r         -> Added {added} chunks [Total in store: {store.count()}]")
            total_chunks += added
            success += 1

        except Exception as e:
            print(f"         -> FAILED: {e}")
            import traceback; traceback.print_exc()
            sys.exit(1)

    print(f"\n{'='*60}")
    print("Ingestion Complete!")
    print(f"{'='*60}")
    print(f"  Processed : {total}")
    print(f"  Succeeded : {success}")
    print(f"  Skipped   : {skipped} (already exists or empty)")
    print(f"  Failed    : {failed}")
    print(f"  Chunks    : {total_chunks} added | {store.count()} total in index")
    print(f"{'='*60}")

    if success == 0:
        sys.exit(1)

    print(f"\n{'='*60}")
    print("Next: commit the new page-preserving FAISS index to Git")
    print(f"{'='*60}")
    print(f"  git add chroma_db/")
    print(f'  git commit -m "chore: rebuild FAISS index with page numbers ({total_chunks} chunks)"')
    print(f"  git push")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
