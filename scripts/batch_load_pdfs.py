"""
Batch load PDFs from /data/pdfs folder into the RAG vector store.

Usage:
    python scripts/batch_load_pdfs.py
    python scripts/batch_load_pdfs.py --folder /path/to/pdfs
    python scripts/batch_load_pdfs.py --cleanup  (remove processed PDFs)
"""

import asyncio
import sys
import os
from pathlib import Path
import argparse
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rag_service import rag_service
from app.services.pdf_processor import PDFProcessor


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
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


async def load_pdfs_from_folder(pdf_folder: str) -> Dict[str, int]:
    """
    Load all PDFs from a folder into the RAG vector store.
    
    Args:
        pdf_folder: Path to folder containing PDFs
        
    Returns:
        Dictionary with stats (total, success, failed, skipped)
    """
    pdf_folder = Path(pdf_folder)
    
    if not pdf_folder.exists():
        print_error(f"Folder not found: {pdf_folder}")
        return {"total": 0, "success": 0, "failed": 0, "skipped": 0}
    
    # Find all PDF files
    pdf_files = list(pdf_folder.glob("*.pdf"))
    
    if not pdf_files:
        print_warning(f"No PDF files found in {pdf_folder}")
        return {"total": 0, "success": 0, "failed": 0, "skipped": 0}
    
    print_info(f"Found {len(pdf_files)} PDF files to process")
    
    stats = {"total": len(pdf_files), "success": 0, "failed": 0, "skipped": 0}
    pdf_processor = PDFProcessor()
    
    for i, pdf_file in enumerate(pdf_files, 1):
        try:
            print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
            
            # Read PDF file
            with open(pdf_file, "rb") as f:
                pdf_content = f.read()
            
            # Extract text
            text, metadata = pdf_processor.extract_text_from_pdf(pdf_content)
            
            if not text or len(text.strip()) < 100:
                print_warning(f"Skipped (insufficient text): {pdf_file.name}")
                stats["skipped"] += 1
                continue
            
            # Prepare document
            document = {
                "id": f"pdf_{pdf_file.stem}",
                "content": text,
                "source": f"pdf:{pdf_file.name}",
                "metadata": {
                    "filename": pdf_file.name,
                    "size_bytes": pdf_file.stat().st_size,
                    "pages": len(text.split("\n\n")),  # Rough estimate
                    **metadata
                }
            }
            
            # Add to RAG
            result = await rag_service.add_documents([document])
            
            if result.get("added", 0) > 0:
                print_success(f"Added to RAG: {pdf_file.name} ({len(text)} chars)")
                stats["success"] += 1
            else:
                print_warning(f"Failed to add: {pdf_file.name}")
                stats["failed"] += 1
                
        except Exception as e:
            print_error(f"Error processing {pdf_file.name}: {str(e)}")
            stats["failed"] += 1
    
    return stats


async def main():
    parser = argparse.ArgumentParser(
        description="Batch load PDFs into LegalHub RAG vector store"
    )
    parser.add_argument(
        "--folder",
        default="c:\\Users\\DESTO\\Desktop\\legalhub-backend\\data\\pdfs",
        help="Path to PDF folder (default: /data/pdfs)"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove PDFs after successful ingestion"
    )
    
    args = parser.parse_args()
    
    print_header("🚀 PDF Batch Loader for LegalHub RAG")
    print_info(f"PDF Folder: {args.folder}")
    print_info(f"Cleanup after processing: {args.cleanup}")
    
    # Load PDFs
    stats = await load_pdfs_from_folder(args.folder)
    
    # Print summary
    print_header("📊 Processing Summary")
    print(f"  Total files:    {stats['total']}")
    print(f"  {Colors.OKGREEN}Success:      {stats['success']}{Colors.ENDC}")
    print(f"  {Colors.FAIL}Failed:        {stats['failed']}{Colors.ENDC}")
    print(f"  {Colors.WARNING}Skipped:       {stats['skipped']}{Colors.ENDC}")
    
    if stats["success"] == 0 and stats["total"] > 0:
        print_error("No PDFs were successfully processed!")
        return 1
    
    if stats["success"] > 0:
        print_success(f"Successfully ingested {stats['success']} PDFs into RAG!")
    
    # Cleanup if requested
    if args.cleanup and stats["success"] > 0:
        print_header("🗑️ Cleaning Up")
        pdf_folder = Path(args.folder)
        pdf_files = list(pdf_folder.glob("*.pdf"))
        
        for pdf_file in pdf_files:
            try:
                pdf_file.unlink()
                print_success(f"Removed: {pdf_file.name}")
            except Exception as e:
                print_error(f"Failed to remove {pdf_file.name}: {str(e)}")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Batch loading interrupted by user.{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
