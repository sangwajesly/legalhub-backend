import sys
from unittest.mock import MagicMock, AsyncMock, patch

# Mock faiss and other dependencies BEFORE importing app/services
faiss_mock = MagicMock()
faiss_mock.__spec__ = MagicMock()
sys.modules["faiss"] = faiss_mock
st_mock = MagicMock()
st_mock.__spec__ = MagicMock()
sys.modules["sentence_transformers"] = st_mock

# Now import the service to test
from app.services import pdf_ingestion_service
from app.services.rag_service import rag_service

import pytest
from pathlib import Path

@pytest.mark.asyncio
async def test_load_pdfs_from_folder_success(tmp_path):
    # Create a dummy PDF file
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    pdf_file = pdf_dir / "test.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 dummy content")
    
    # Mock PDFProcessor
    with patch("app.services.pdf_ingestion_service.PDFProcessor") as MockPDFProcessor:
        mock_processor = MockPDFProcessor.return_value
        mock_processor.extract_text_from_pdf.return_value = ("Extracted text content" * 10, {"author": "me"})
        
        # Mock rag_service.add_documents
        with patch.object(rag_service, "add_documents", new_callable=AsyncMock) as mock_add:
            mock_add.return_value = {"added": 1, "skipped": 0}
            
            # Run the service
            stats = await pdf_ingestion_service.load_pdfs_from_folder(str(pdf_dir))
            
            # Verify
            assert stats["total"] == 1
            assert stats["success"] == 1
            
            # Verify RAG service called
            mock_add.assert_called_once()
            call_args = mock_add.call_args[0][0] # List of docs
            assert len(call_args) == 1
            assert call_args[0]["id"] == "pdf_test"
            assert call_args[0]["content"] == "Extracted text content" * 10

@pytest.mark.asyncio
async def test_load_pdfs_no_folder():
    stats = await pdf_ingestion_service.load_pdfs_from_folder("/non/existent/path")
    assert stats["total"] == 0

@pytest.mark.asyncio
async def test_load_pdfs_empty_file(tmp_path):
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    pdf_file = pdf_dir / "empty.pdf"
    pdf_file.write_bytes(b"")

    with patch("app.services.pdf_ingestion_service.PDFProcessor") as MockPDFProcessor:
        mock_processor = MockPDFProcessor.return_value
        # Return empty text
        mock_processor.extract_text_from_pdf.return_value = ("", {})
        
        stats = await pdf_ingestion_service.load_pdfs_from_folder(str(pdf_dir))
        
        assert stats["total"] == 1
        assert stats["skipped"] == 1 # Should be skipped due to < 100 chars
