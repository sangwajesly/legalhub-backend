from pathlib import Path
import os

CHROMA = Path(__file__).resolve().parent.parent / 'chroma_db'
FAISS = CHROMA / 'legalhub_documents.faiss'
PKL   = CHROMA / 'legalhub_documents_docs.pkl'

for p in (FAISS, PKL):
    if p.exists():
        size = p.stat().st_size / (1024*1024)
        print(f"{p} -> {size:.2f} MB")
    else:
        print(f"{p} -> not found")

# advise
if FAISS.exists():
    if FAISS.stat().st_size > 50 * 1024 * 1024:
        print('\nRecommendation: file >50MB — use Git LFS or store as release asset/S3.')
    else:
        print('\nRecommendation: file size looks reasonable for LFS but consider LFS for safety.')
