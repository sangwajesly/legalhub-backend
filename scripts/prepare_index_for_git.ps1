# Prepare FAISS index files for Git (Windows PowerShell)
# Usage: From repo root run: .\scripts\prepare_index_for_git.ps1

$chromaDir = Join-Path $PSScriptRoot "..\chroma_db" | Resolve-Path -Relative
$faiss = Join-Path $chromaDir "legalhub_documents.faiss"
$pkl = Join-Path $chromaDir "legalhub_documents_docs.pkl"

Write-Host "Checking chroma_db files..."
if (-Not (Test-Path $faiss) -and -Not (Test-Path $pkl)) {
    Write-Host "No FAISS files found at $chromaDir. Run ingestion first." -ForegroundColor Yellow
    exit 1
}

# Show sizes
Get-Item $faiss, $pkl | ForEach-Object {
    if ($_ -ne $null) {
        $szMB = [math]::Round($_.Length / 1MB, 2)
        Write-Host "Found: $($_.FullName) -> $szMB MB"
    }
}

# Git LFS check
$gitLfs = git lfs version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "git-lfs not found. Install Git LFS first: https://git-lfs.com/" -ForegroundColor Yellow
    Write-Host "Then run: git lfs install`n"
    exit 1
}

Write-Host "Tracking '*.faiss' and '*_docs.pkl' with Git LFS..."
git lfs track "*.faiss"
git lfs track "*_docs.pkl"

Write-Host "The .gitattributes file has been updated. Review and commit the following files:"
Write-Host "  .gitattributes"
Write-Host "  chroma_db/legalhub_documents.faiss"
Write-Host "  chroma_db/legalhub_documents_docs.pkl"

Write-Host "To add and push (example):"
Write-Host "  git add .gitattributes chroma_db/legalhub_documents.faiss chroma_db/legalhub_documents_docs.pkl"
Write-Host "  git commit -m 'chore: add FAISS index via LFS'"
Write-Host "  git push"
