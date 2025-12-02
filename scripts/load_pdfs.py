#!/usr/bin/env python
"""
Batch PDF Loader Script for LegalHub RAG System

This script loads all PDFs from the /data/pdfs folder into the ChromaDB vector store.
Use this for bulk ingestion of legal documents.

Usage:
    python scripts/load_pdfs.py [--collection-name legalhub_documents] [--chunk-size 1000] [--chunk-overlap 200]

Example:
    python scripts/load_pdfs.py
    python scripts/load_pdfs.py --collection-name legal_docs --chunk-size 1500
"""

import asyncio
import os
import sys
import argparse
from pathlib import Path
from typing import List
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ingestion_service import ingest_pdf
from app.config import settings

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")


def print_success(text: str):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text: str):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


async def load_pdfs(
    pdf_folder: Path,
    collection_name: str = "legalhub_documents",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> dict:
    """
    Batch load all PDFs from a folder into ChromaDB.
    
    Args:
        pdf_folder: Path to folder containing PDFs
        collection_name: ChromaDB collection to store in
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
        
    Returns:
        Summary dict with load results
    """
    
    # Validate folder
    if not pdf_folder.exists():
        print_error(f"PDF folder not found: {pdf_folder}")
        return {"success": False, "error": "Folder not found"}
    
    # Find all PDFs
    pdf_files = list(pdf_folder.glob("*.pdf"))
    
    if not pdf_files:
        print_warning(f"No PDF files found in {pdf_folder}")
        return {"success": False, "error": "No PDFs found", "pdf_count": 0}
    
    print_info(f"Found {len(pdf_files)} PDF files to load")
    
    # Load each PDF
    results = {
        "success": True,
        "total": len(pdf_files),
        "loaded": 0,
        "failed": 0,
        "failed_files": [],
        "loaded_files": [],
        "total_chunks": 0,
    }
    
    for pdf_path in pdf_files:
        print_info(f"Loading: {pdf_path.name}")
        
        try:
            # Prepare metadata
            metadata = {
                "source_file": pdf_path.name,
                "ingested_at": datetime.now().isoformat(),
            }
            
            # Ingest PDF
            result = await ingest_pdf(
                pdf_path=str(pdf_path),
                collection_name=collection_name,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                metadata=metadata,
            )
            
            chunks = result.get("n_chunks", 0)
            results["loaded"] += 1
            results["total_chunks"] += chunks
            results["loaded_files"].append({
                "name": pdf_path.name,
                "chunks": chunks,
                "size_mb": pdf_path.stat().st_size / (1024 * 1024),
            })
            
            print_success(f"Loaded {pdf_path.name} ({chunks} chunks)")
            
        except Exception as e:
            print_error(f"Failed to load {pdf_path.name}: {str(e)}")
            results["failed"] += 1
            results["failed_files"].append({
                "name": pdf_path.name,
                "error": str(e),
            })
    
    return results


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Batch load PDFs from /data/pdfs into ChromaDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/load_pdfs.py
  python scripts/load_pdfs.py --collection-name legal_docs
  python scripts/load_pdfs.py --chunk-size 1500 --chunk-overlap 300
        """
    )
    
    parser.add_argument(
        "--pdf-folder",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "pdfs",
        help="Path to folder containing PDFs (default: ./data/pdfs)",
    )
    parser.add_argument(
        "--collection-name",
        default="legalhub_documents",
        help="ChromaDB collection name (default: legalhub_documents)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="Text chunk size in characters (default: 1000)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=200,
        help="Chunk overlap in characters (default: 200)",
    )
    
    args = parser.parse_args()
    
    # Print header
    print_header("LegalHub RAG - Batch PDF Loader")
    print_info(f"PDF Folder: {args.pdf_folder}")
    print_info(f"Collection: {args.collection_name}")
    print_info(f"Chunk Size: {args.chunk_size}, Overlap: {args.chunk_overlap}")
    print_info(f"ChromaDB Path: {settings.CHROMADB_PATH}")
    
    # Load PDFs
    results = await load_pdfs(
        pdf_folder=args.pdf_folder,
        collection_name=args.collection_name,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    
    # Print results
    print_header("Load Results")
    print(f"Total PDFs: {results['total']}")
    print(f"Loaded: {results['loaded']}")
    print(f"Failed: {results['failed']}")
    print(f"Total Chunks: {results['total_chunks']}")
    
    if results["loaded_files"]:
        print_header("Successfully Loaded Files")
        for file_info in results["loaded_files"]:
            print(f"  • {file_info['name']}: {file_info['chunks']} chunks ({file_info['size_mb']:.2f} MB)")
    
    if results["failed_files"]:
        print_header("Failed Files")
        for file_info in results["failed_files"]:
            print(f"  • {file_info['name']}: {file_info['error']}")
    
    # Final status
    if results["success"] and results["failed"] == 0:
        print_success(f"Successfully loaded all {results['loaded']} PDFs ({results['total_chunks']} chunks)")
        return 0
    elif results["loaded"] > 0:
        print_warning(f"Loaded {results['loaded']} PDFs with {results['failed']} failures")
        return 1
    else:
        print_error("Failed to load any PDFs")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_warning("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
