"""
Direct PDF Ingestion Script for LegalHub RAG
============================================
Bypasses the Gemini LLM classification step entirely.
Loads ALL PDFs from /data/pdfs directly into the FAISS vector store
using local SentenceTransformer embeddings (no API calls required).

Usage:
    uv run python scripts/ingest_pdfs_direct.py
    uv run python scripts/ingest_pdfs_direct.py --reset   (clear store first)
"""

import sys
import os
import re
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Infer document type from filename - no API needed
def classify_by_filename(filename: str) -> dict:
    name = filename.lower()
    if "constitution" in name:
        return {"document_type": "Constitution", "legal_domain": "Constitutional Law", "jurisdiction": "Cameroon"}
    elif "penal" in name or "criminal" in name:
        return {"document_type": "Statute", "legal_domain": "Criminal Law", "jurisdiction": "Cameroon"}
    elif "electoral" in name:
        return {"document_type": "Statute", "legal_domain": "Administrative Law", "jurisdiction": "Cameroon"}
    elif "mining" in name:
        return {"document_type": "Statute", "legal_domain": "Corporate Law", "jurisdiction": "Cameroon"}
    elif "finance" in name or "budget" in name:
        return {"document_type": "Statute", "legal_domain": "Administrative Law", "jurisdiction": "Cameroon"}
    elif "customary" in name or "women" in name or "family" in name:
        return {"document_type": "Other", "legal_domain": "Family Law", "jurisdiction": "Cameroon"}
    else:
        return {"document_type": "Statute", "legal_domain": "Other", "jurisdiction": "Cameroon"}


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Direct PDF ingestion into FAISS (no Gemini calls)")
    parser.add_argument("--pdf-folder", default=str(Path(__file__).parent.parent / "data" / "pdfs"),
                        help="Path to PDF folder")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Characters per chunk")
    parser.add_argument("--overlap", type=int, default=200, help="Overlap between chunks")
    parser.add_argument("--reset", action="store_true", help="Reset the vector store before ingesting")
    args = parser.parse_args()

    pdf_folder = Path(args.pdf_folder)
    if not pdf_folder.exists():
        print(f"ERROR: PDF folder not found: {pdf_folder}")
        sys.exit(1)

    pdf_files = list(pdf_folder.glob("*.pdf"))
    if not pdf_files:
        print(f"ERROR: No PDF files found in {pdf_folder}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"LegalHub Direct PDF Ingestion")
    print(f"{'='*60}")
    print(f"PDF Folder : {pdf_folder}")
    print(f"PDFs Found : {len(pdf_files)}")
    print(f"Chunk Size : {args.chunk_size} chars  |  Overlap: {args.overlap} chars")
    print(f"{'='*60}\n")

    # Import FAISS store and PDF processor
    from app.utils.faiss_store import get_vector_store
    from app.services.pdf_processor import PDFProcessor

    vector_store = get_vector_store("legalhub_documents")

    if args.reset:
        print("Resetting vector store...")
        vector_store.reset()
        print("Vector store cleared.\n")

    pdf_processor = PDFProcessor()

    total = len(pdf_files)
    success = 0
    skipped = 0
    failed = 0
    total_chunks = 0

    for i, pdf_path in enumerate(sorted(pdf_files), 1):
        print(f"[{i}/{total}] Processing: {pdf_path.name}")
        try:
            with open(pdf_path, "rb") as f:
                pdf_content = f.read()

            text, metadata = pdf_processor.extract_text_from_pdf(pdf_content)

            if not text or len(text.strip()) < 100:
                print(f"         -> SKIPPED (insufficient text - likely scanned/image PDF)")
                skipped += 1
                continue

            # Classify by filename (no API)
            classification = classify_by_filename(pdf_path.name)

            # Create chunks
            chunks = chunk_text(text, args.chunk_size, args.overlap)
            print(f"         -> Extracted {len(text):,} chars  |  {len(chunks)} chunks")
            print(f"         -> Type: {classification['document_type']}  |  Domain: {classification['legal_domain']}")

            # Prepare documents for FAISS
            documents = []
            doc_id = re.sub(r"[^a-zA-Z0-9_]", "_", pdf_path.stem)[:60]
            for j, chunk in enumerate(chunks):
                doc = {
                    "id": f"{doc_id}_chunk_{j}",
                    "content": chunk,
                    "source": f"pdf:{pdf_path.name}",
                    "filename": pdf_path.name,
                    "document_type": classification["document_type"],
                    "legal_domain": classification["legal_domain"],
                    "jurisdiction": classification["jurisdiction"],
                    "chunk_index": j,
                }
                documents.append(doc)

            # Add to FAISS in batches of 50
            batch_size = 50
            added = 0
            for k in range(0, len(documents), batch_size):
                batch = documents[k:k+batch_size]
                result = vector_store.add_documents(batch)
                added += result.get("added", 0)

            print(f"         -> Added {added} chunks to FAISS  [Total in store: {vector_store.count()}]")
            total_chunks += added
            success += 1

        except Exception as e:
            print(f"         -> FAILED: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Ingestion Complete!")
    print(f"{'='*60}")
    print(f"  Processed : {total}")
    print(f"  Succeeded : {success}")
    print(f"  Skipped   : {skipped}  (image/scanned PDFs - no extractable text)")
    print(f"  Failed    : {failed}")
    print(f"  Chunks    : {total_chunks} total chunks added to FAISS")
    print(f"  Store Size: {vector_store.count()} documents in index")
    print(f"{'='*60}\n")

    if success == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
