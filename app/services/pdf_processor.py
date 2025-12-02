"""
Service for robust text extraction from PDF documents.
"""

from pypdf import PdfReader
from typing import List, Dict, Any, Tuple
import io


class PDFProcessor:
    """
    Handles text and metadata extraction from PDF documents.
    """

    @staticmethod
    def extract_text_from_pdf(pdf_content: bytes) -> Tuple[str, Dict[str, Any]]:
        """
        Extracts text and metadata from PDF content.

        Args:
            pdf_content: The binary content of the PDF file.

        Returns:
            A tuple containing:
            - The extracted text content as a single string.
            - A dictionary of extracted metadata.
        """
        reader = PdfReader(io.BytesIO(pdf_content))

        # Extract text
        text_content = ""
        for page in reader.pages:
            text_content += page.extract_text() + "\n"  # Add newline between pages

        # Extract metadata
        metadata = reader.metadata
        if metadata:
            metadata = {k: str(v) for k, v in metadata.items()}
        else:
            metadata = {}

        return text_content, metadata

    @staticmethod
    def extract_text_by_page(pdf_content: bytes) -> List[str]:
        """
        Extracts text from each page of a PDF document.

        Args:
            pdf_content: The binary content of the PDF file.

        Returns:
            A list of strings, where each string is the text from a single page.
        """
        reader = PdfReader(io.BytesIO(pdf_content))
        page_texts = [page.extract_text() for page in reader.pages]
        return page_texts

    # Future improvements:
    # - OCR for scanned PDFs
    # - More sophisticated layout analysis for tables, columns, etc.
    # - LLM-driven metadata extraction (e.g., identifying document type, parties, dates)
