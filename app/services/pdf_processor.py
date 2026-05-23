"""
Service for robust text extraction from PDF documents.
"""

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    PdfReader = None

from typing import List, Dict, Any, Tuple
import io
import logging

logger = logging.getLogger(__name__)


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
        if not PYPDF_AVAILABLE:
            logger.warning("pypdf not installed. PDF extraction disabled.")
            return "", {}

        try:
            reader = PdfReader(io.BytesIO(pdf_content))

            # Extract text
            text_content = ""
            for page in reader.pages:
                text_content += (page.extract_text() or "") + "\n"

            # Extract metadata
            metadata = reader.metadata
            if metadata:
                metadata = {k: str(v) for k, v in metadata.items()}
            else:
                metadata = {}

            return text_content, metadata
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return "", {}

    @staticmethod
    def extract_text_by_page(pdf_content: bytes) -> List[str]:
        """
        Extracts text from each page of a PDF document.

        Args:
            pdf_content: The binary content of the PDF file.

        Returns:
            A list of strings, where each string is the text from a single page.
        """
        if not PYPDF_AVAILABLE:
            return []

        try:
            reader = PdfReader(io.BytesIO(pdf_content))
            page_texts = [(page.extract_text() or "") for page in reader.pages]
            return page_texts
        except Exception as e:
            logger.error(f"Error extracting PDF pages: {e}")
            return []

    @staticmethod
    async def classify_legal_document(text_sample: str) -> Dict[str, str]:
        """
        Uses the Gemini model to classify a legal document text sample.

        Args:
            text_sample: A sample text from the start of the document.

        Returns:
            A dictionary containing document_type, legal_domain, jurisdiction, and summary.
        """
        from app.services.gemini_service import send_message
        import json

        # Take first 3000 characters
        sample = text_sample[:3000]

        prompt = f"""
Analyze the following legal document excerpt and classify it.
You MUST respond with a raw JSON object containing EXACTLY these four keys and no other text:
- "document_type": Choose one from ["Statute", "Decree", "Court Decision", "Treaty", "Constitution", "Other"]
- "legal_domain": Choose one from ["Criminal Law", "Civil Law", "Labour Law", "Family Law", "Human Rights", "Corporate Law", "Constitutional Law", "Administrative Law", "Other"]
- "jurisdiction": Choose one from ["Cameroon", "Central Africa", "International", "Other"]
- "summary": A concise 1 to 2 sentence summary of what this document covers.

Legal Excerpt:
---------------------
{sample}
---------------------

Your JSON response:
"""
        try:
            result = await send_message(prompt)
            response_text = result.get("response", "").strip()

            # Clean response text in case it has markdown code block backticks
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            classification = json.loads(response_text)

            return {
                "document_type": classification.get("document_type", "Other"),
                "legal_domain": classification.get("legal_domain", "Other"),
                "jurisdiction": classification.get("jurisdiction", "Other"),
                "summary": classification.get("summary", "No summary available.")
            }
        except Exception as e:
            logger.error(f"Failed to classify legal document via LLM: {e}")
            return {
                "document_type": "Other",
                "legal_domain": "Other",
                "jurisdiction": "Other",
                "summary": "Legal document."
            }

