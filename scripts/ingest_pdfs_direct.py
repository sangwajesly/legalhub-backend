"""
Direct PDF Ingestion Script for LegalHub RAG
============================================
Self-contained: imports NOTHING from app.* — avoids Python 3.12/Windows
incompatibilities in the google/transformers/jinja2 dependency chain.

Usage:
    uv run python scripts/ingest_pdfs_direct.py
    uv run python scripts/ingest_pdfs_direct.py --reset
"""

import sys
import os
import re
import pickle
import logging
import argparse
from pathlib import Path

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Minimal config — read CHROMADB_PATH from .env without importing app.config
# ---------------------------------------------------------------------------
def _read_env() -> dict:
    env = {}
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env

_ENV = _read_env()
CHROMADB_PATH = _ENV.get("CHROMADB_PATH", str(PROJECT_ROOT / "chroma_db"))

# ---------------------------------------------------------------------------
# PDF extraction (inline — no app.services import)
# ---------------------------------------------------------------------------
def extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io_module.BytesIO(pdf_bytes))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)
        return "\n".join(pages)
    except Exception as e:
        logger.warning(f"pypdf extraction failed: {e}")
        return ""

import io as io_module  # needed above

# ---------------------------------------------------------------------------
# Document classification (filename-based, no API)
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
# Minimal FAISS wrapper (no app.utils import)
# ---------------------------------------------------------------------------
class DirectFAISSStore:
    def __init__(self, path: str, name: str = "legalhub_documents", dim: int = 384):
        self.path = path
        self.name = name
        self.dim = dim
        self.index = None
        self.documents = []
        self._faiss = None
        self._np = None
        self._model = None

    def _paths(self):
        os.makedirs(self.path, exist_ok=True)
        return (
            os.path.join(self.path, f"{self.name}.faiss"),
            os.path.join(self.path, f"{self.name}_docs.pkl"),
        )

    def init(self):
        """Load heavy deps and existing index."""
        import faiss
        import numpy as np
        from sentence_transformers import SentenceTransformer

        self._faiss = faiss
        self._np = np
        self._model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.IndexFlatL2(self.dim)

        idx_path, docs_path = self._paths()
        if os.path.exists(idx_path) and os.path.exists(docs_path):
            try:
                self.index = faiss.read_index(idx_path)
                with open(docs_path, "rb") as f:
                    self.documents = pickle.load(f)
                print(f"[OK] Loaded existing index: {len(self.documents)} chunks")
            except Exception as e:
                print(f"[WARN] Could not load existing index: {e}. Starting fresh.")
        else:
            print("[OK] No existing index — starting fresh.")

    def reset(self):
        self.index = self._faiss.IndexFlatL2(self.dim)
        self.documents = []
        self._save()
        print("[OK] Index reset (empty).")

    def add(self, docs: list) -> int:
        texts = [d["content"] for d in docs]
        embeddings = self._model.encode(texts, show_progress_bar=False)
        self.index.add(self._np.array(embeddings, dtype="float32"))
        self.documents.extend(docs)
        self._save()
        return len(docs)

    def count(self) -> int:
        return len(self.documents)

    def _save(self):
        idx_path, docs_path = self._paths()
        self._faiss.write_index(self.index, idx_path)
        with open(docs_path, "wb") as f:
            pickle.dump(self.documents, f)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Direct PDF ingestion into FAISS")
    parser.add_argument("--pdf-folder", default=str(PROJECT_ROOT / "data" / "pdfs"))
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--overlap", type=int, default=200)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    pdf_folder = Path(args.pdf_folder)
    if not pdf_folder.exists():
        print(f"ERROR: PDF folder not found: {pdf_folder}")
        sys.exit(1)

    pdf_files = sorted(pdf_folder.glob("*.pdf"))
    if not pdf_files:
        print(f"ERROR: No PDFs in {pdf_folder}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("LegalHub Direct PDF Ingestion")
    print(f"{'='*60}")
    print(f"PDF Folder : {pdf_folder}")
    print(f"PDFs Found : {len(pdf_files)}")
    print(f"Chunk Size : {args.chunk_size} chars  |  Overlap: {args.overlap} chars")
    print(f"FAISS Path : {CHROMADB_PATH}")
    print(f"{'='*60}\n")

    print("Loading embedding model (this may take ~30s on first run)...")
    store = DirectFAISSStore(CHROMADB_PATH)
    store.init()

    if args.reset:
        print("Resetting vector store...")
        store.reset()
        print()

    total = len(pdf_files)
    success = skipped = failed = total_chunks = 0

    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"[{i}/{total}] {pdf_path.name}")
        try:
            pdf_bytes = pdf_path.read_bytes()
            text = extract_pdf_text(pdf_bytes)

            if not text or len(text.strip()) < 100:
                print(f"         -> SKIPPED (insufficient text — likely scanned PDF)")
                skipped += 1
                continue

            clf = classify_by_filename(pdf_path.name)
            chunks = chunk_text(text, args.chunk_size, args.overlap)
            print(f"         -> {len(text):,} chars | {len(chunks)} chunks | {clf['legal_domain']}")

            doc_id = re.sub(r"[^a-zA-Z0-9_]", "_", pdf_path.stem)[:60]
            documents = [
                {
                    "id": f"{doc_id}_chunk_{j}",
                    "content": chunk,
                    "source": f"pdf:{pdf_path.name}",
                    "filename": pdf_path.name,
                    "document_type": clf["document_type"],
                    "legal_domain": clf["legal_domain"],
                    "jurisdiction": "Cameroon",
                    "chunk_index": j,
                }
                for j, chunk in enumerate(chunks)
            ]

            # Add in batches of 50
            added = 0
            for k in range(0, len(documents), 50):
                added += store.add(documents[k:k+50])

            print(f"         -> Added {added} chunks  [Total: {store.count()}]")
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
    print("Next: commit the index to Git so Vercel picks it up")
    print(f"{'='*60}")
    print(f"  git add chroma_db/")
    print(f'  git commit -m "chore: update FAISS index ({total_chunks} chunks)"')
    print(f"  git push")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
