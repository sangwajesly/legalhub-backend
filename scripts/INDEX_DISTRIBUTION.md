# FAISS Index Distribution Options

This document explains safe ways to store and distribute the FAISS index (`*.faiss`) and the documents metadata (`*_docs.pkl`) so the hosted project can load them without re-running embedding.

Options

1. Git LFS (recommended for repo-hosted index)
   - Use Git LFS to avoid bloating the repo history.
   - Steps (Windows PowerShell):
     ```powershell
     # from repo root
     .\scripts\prepare_index_for_git.ps1
     git add .gitattributes chroma_db/legalhub_documents.faiss chroma_db/legalhub_documents_docs.pkl
     git commit -m "chore: add FAISS index via LFS"
     git push
     ```
   - Pros: Simple; index comes with each deploy where Git LFS is supported.
   - Cons: Repo requires LFS; large files may count against LFS quota.

2. Release asset / object storage (S3, GCS)
   - Upload the index files to an S3 bucket or GitHub Release asset.
   - Modify deploy or app startup to download and extract the files at runtime before loading.
   - Pros: Works for large indexes; decouples repo size from index.
   - Cons: Need credentials to download at deploy/runtime, or public bucket.

3. Containerize the app with FAISS pre-installed (recommended for hosts without native libs)
   - Build a Docker image that installs `faiss-cpu` and includes the index files.
   - Use the image for deployment (e.g., AWS ECS, DigitalOcean App Platform, Heroku container registry).

Dockerfile snippet (minimal):

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN pip install --upgrade pip
RUN pip install faiss-cpu
RUN pip install -r requirements.txt

COPY . /app
# If you added index files to chroma_db, they'll be copied into the image.
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

Notes and safety

- The app already gracefully falls back if the index files are missing or unreadable.
- Verify `faiss-cpu` version parity between dev and prod to avoid binary incompatibilities.
- Always review `*_docs.pkl` for sensitive info before pushing.

Hybrid deployment note

- You can keep local FAISS + `*.pkl` files for offline thesis-defense usage while using a hosted vector DB in production.
- A hosted vector DB stores vectors and metadata directly; it does not store the raw `.faiss` or `.pkl` files as records.
- Use local FAISS for offline mode and switch to remote vector storage via environment configuration when the network is available.

Questions

- Do you want me to create a short Dockerfile in the repo and add a small startup downloader (S3) as an optional utility?
