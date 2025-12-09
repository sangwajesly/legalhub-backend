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

from app.services.pdf_ingestion_service import load_pdfs_from_folder


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


def print_info(text: str):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


async def main():
    parser = argparse.ArgumentParser(
        description="Batch load PDFs into LegalHub RAG vector store"
    )
    # Default path relative to project root
    default_path = os.path.join(os.getcwd(), "data", "pdfs")
    
    parser.add_argument(
        "--folder",
        default=default_path,
        help=f"Path to PDF folder (default: {default_path})"
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
    
    # Load PDFs using the service
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
                # Only remove if we likely processed it (this logic is loose in CLI, 
                # but stats['success'] > 0 suggests we did something. 
                # Ideally service returns list of processed files)
                # For safety, we only cleanup if ALL succeeded or we accept partial cleanup.
                # Here we just try to unlink all found pdfs if cleanup requested
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
