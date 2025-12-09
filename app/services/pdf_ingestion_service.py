"""
Service for ingesting PDFs into the RAG system.
"""

import logging
import os
from pathlib import Path
from typing import Dict

from app.services.rag_service import rag_service
from app.services.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)

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
        logger.error(f"Folder not found: {pdf_folder}")
        return {"total": 0, "success": 0, "failed": 0, "skipped": 0}
    
    # Find all PDF files
    pdf_files = list(pdf_folder.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {pdf_folder}")
        return {"total": 0, "success": 0, "failed": 0, "skipped": 0}
    
    logger.info(f"Found {len(pdf_files)} PDF files to process in {pdf_folder}")
    
    stats = {"total": len(pdf_files), "success": 0, "failed": 0, "skipped": 0}
    pdf_processor = PDFProcessor()
    
    for i, pdf_file in enumerate(pdf_files, 1):
        try:
            logger.info(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
            
            # Read PDF file
            with open(pdf_file, "rb") as f:
                pdf_content = f.read()
            
            # Extract text
            text, metadata = pdf_processor.extract_text_from_pdf(pdf_content)
            
            if not text or len(text.strip()) < 100:
                logger.warning(f"Skipped (insufficient text): {pdf_file.name}")
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
                logger.info(f"Added to RAG: {pdf_file.name} ({len(text)} chars)")
                stats["success"] += 1
            else:
                logger.warning(f"Failed to add: {pdf_file.name}")
                stats["failed"] += 1
                
        except Exception as e:
            logger.error(f"Error processing {pdf_file.name}: {str(e)}")
            stats["failed"] += 1
    
    return stats

def extract_text_from_pdf(pdf_path: str) -> str:
    """Helper to extract text from a single PDF file."""
    try:
        pdf_processor = PDFProcessor()
        with open(pdf_path, "rb") as f:
            content = f.read()
        text, _ = pdf_processor.extract_text_from_pdf(content)
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {e}")
        return ""
